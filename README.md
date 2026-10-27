# Shop Pricing API: демо CI/CD та Continuous Testing

Невеликий REST API на **Python + FastAPI**, який рахує вартість замовлення (товари, знижка за опт, промокоди).
БД не використовується: товари зберігаються в пам'яті, тому демо не залежить від інфраструктури.

## Структура

```
app/
  pricing.py        чиста бізнес-логіка (знижки, промокоди)       ← unit-тести
  repository.py     in-memory сховище товарів
  models.py         Pydantic-моделі (валідація запитів)
  main.py           HTTP-ендпоїнти                                 ← integration-тести
tests/
  unit/             ізольовані тести логіки, без HTTP
  integration/      весь застосунок через TestClient (HTTP у пам'яті)
  smoke/            тести проти РЕАЛЬНО запущеного сервісу (BASE_URL)
Dockerfile
.github/workflows/
  ci.yml            CI + Continuous Testing
  cd.yml            CD: GHCR → staging → production
```

## Ендпоїнти

| Метод | Шлях              | Опис                                    |
|-------|-------------------|-----------------------------------------|
| GET   | `/health`         | стан сервісу та версія (git SHA)        |
| GET   | `/products`       | список товарів                          |
| GET   | `/products/{id}`  | один товар                              |
| POST  | `/products`       | створити товар                          |
| POST  | `/orders/quote`   | розрахунок вартості замовлення          |

Swagger UI: http://localhost:8000/docs

## Локальний запуск

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload     # запуск API

ruff check . && ruff format --check .          # лінтер
pytest tests/unit                              # unit
pytest tests/integration                       # integration
pytest tests/unit tests/integration --cov      # покриття (поріг 90%)

# smoke проти запущеного сервісу (PowerShell):
$env:BASE_URL="http://localhost:8000"; pytest tests/smoke
```

Docker:
```bash
docker build -t shop-api .
docker run -p 8000:8000 shop-api
```

## Пайплайн

```
            ┌──────────────────────── CI (ci.yml) ────────────────────────┐
push / PR → │ lint → unit (py3.12, 3.13) → integration + coverage → docker  │
nightly  →  │                                         build + smoke tests  │
            └──────────────────────────────┬──────────────────────────────┘
                                           │ тільки main і тільки якщо CI зелений
            ┌──────────────────────── CD (cd.yml) ────────────────────────┐
            │ build & push image (GHCR) → deploy staging + smoke           │
            │   → [ручне підтвердження] → deploy production + smoke        │
            └─────────────────────────────────────────────────────────────┘
```

**Де тут Continuous Testing:** тести запускаються автоматично на кожному етапі життя коду, а не один раз:
1. на кожен push у будь-яку гілку;
2. на кожен Pull Request (без зеленого CI злити не можна);
3. щоночі за розкладом (`schedule`), щоб ловити регресії від оновлених залежностей;
4. після кожного деплою (smoke-тести на staging і production);
5. з quality gate: якщо покриття < 90%, збірка падає.

Тести різних рівнів (піраміда): багато швидких unit, менше integration, кілька smoke.

> Деплой у `cd.yml` **симульований**: образ із GHCR запускається на раннері GitHub.
> У реальному проєкті цей крок замінюється на `kubectl set image`, ssh на сервер, Render/Railway deploy hook тощо.

## Гілки

Рекомендований спрощений GitFlow:

| Гілка        | Призначення                         | Що запускається                     |
|--------------|-------------------------------------|-------------------------------------|
| `feature/*`  | розробка окремої фічі               | CI                                  |
| `develop`    | інтеграція фіч                      | CI (PR у develop теж)               |
| `main`       | стабільний код, «прод»              | CI → CD (staging → production)      |

Якщо хочеться простіше, достатньо `main` + `feature/*` (GitHub Flow), бо пайплайн працює і так.

## Налаштування на GitHub (один раз)

1. Створити репозиторій, запушити `main` і `develop`.
2. **Settings → Branches → Branch protection rule** для `main` (і `develop`):
   - *Require a pull request before merging*
   - *Require status checks to pass*: вибрати `Lint (ruff)`, `Unit tests …`, `Integration tests + coverage gate`, `Build Docker image + smoke tests`.
3. **Settings → Environments**: створити `staging` і `production`;
   для `production` увімкнути *Required reviewers* (себе). Це і є ручне підтвердження релізу.

Окремо давати права на GHCR не потрібно: `cd.yml` сам запитує `packages: write` для `GITHUB_TOKEN`.

## Сценарій демонстрації

1. **Зелений шлях.** Гілка `feature/add-promo`: додати в `PROMO_CODES` новий код і тест для нього.
   Push → у вкладці *Actions* видно, як CI проходить усі етапи.
2. **CI ловить баг.** У `app/pricing.py` змінити `BULK_DISCOUNT = Decimal("0.05")` на `Decimal("0.5")`.
   Push → падає `Unit tests`, а наступні етапи не запускаються. Відкрити PR: кнопка Merge заблокована.
3. **Quality gate.** Додати в `pricing.py` функцію без тестів → покриття падає нижче порогу, і `coverage gate` червоний.
4. **CD.** Виправити, змерджити PR у `main` → стартує CD: образ з'являється в *Packages*,
   staging деплоїться автоматично, production чекає кнопки *Review deployments*.
   Після підтвердження smoke-тести перевіряють `/health`, а у відповіді видно версію = SHA коміту.
5. **Continuous Testing за розкладом.** Показати запуски `schedule` у вкладці Actions (або запустити вручну через *Run workflow*).
