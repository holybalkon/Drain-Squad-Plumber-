# Drain Squad Plumber: статичний сайт під SEO/GEO

Сім сторінок, чистий HTML + один CSS + один невеликий JS. Увесь контент лежить у HTML, JS лише додає інтерактив.

```
index.html                  головна (h1 «Professional Drain & Plumbing Services»)
drain-cleaning.html         сторінка послуги
sewer-backup.html           сторінка послуги
emergency-plumbing.html     сторінка послуги
leak-detection.html         сторінка послуги
about.html                  про компанію
404.html                    noindex, без canonical
style.css  script.js        стилі і поведінка (script.js підключено з defer)
robots.txt  sitemap.xml  .htaccess  favicon.svg
logo.svg  logo.png  og-image.png
tools/                      build.py (генерація), qa.py (перевірка), вихідники
```

Перегляд локально: у цій папці `python3 -m http.server 8000`, потім http://localhost:8000. Посилання кореневі (`/about.html`), тому через `file://` вони не працюють.

## Що зроблено за вимогами з документа

- **Статичний HTML без JS-рендеру.** Усі картки, ціни, FAQ, відгуки лежать у розмітці. Скрипт тільки знімає клас `no-js`, згортає FAQ і вмикає стрілки, друк, форму.
- **Заголовки.** Рівно один `<h1>` на сторінку, послідовність h1 → h2 → h3 → h4 без пропусків. Питання FAQ це `<h3>`, картки послуг `<h4>` під `<h3>` групи. Заголовки не використані для стилю.
- **Семантика.** `<header>`, `<nav aria-label>`, `<main id="main-content">` (один), `<section aria-labelledby>`, `<article>`, `<footer>`, skip-link першим елементом, breadcrumbs `<ol>` з `aria-current="page"` на внутрішніх сторінках. Текст у `<p>`/`<li>`, без `<br>` для відступів.
- **`<head>` на кожній сторінці.** title до 60 символів, description 150–160, canonical, `dateModified`, Open Graph (`og:image` і `og:locale`), Twitter Cards, robots, favicon. Блок geo (`geo.placename`, `geo.region`, `ICBM`) з'являється автоматично, коли заповнені місто й координати.
- **JSON-LD.** Головна: `Plumber` (LocalBusiness), `WebSite`, `WebPage`, `ItemList` послуг, `FAQPage`. Сторінки послуг: `Plumber`, `WebPage`, `Service`, `BreadcrumbList`, `FAQPage`. About: `AboutPage` і `BreadcrumbList`. Текст у `FAQPage` збігається з видимим дослівно, перевірка автоматична.
- **FAQ-акордеон.** Кнопка з `aria-expanded` і `aria-controls`, згортання через `grid-template-rows` (не `display:none`). У стані `no-js` усі відповіді відкриті.
- **Технічні файли.** `robots.txt` (Allow, AI-боти не блокуються, посилання на sitemap), `sitemap.xml` (lastmod, changefreq, priority), `.htaccess` (GZIP, кеш, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, 404), SVG-фавікон.
- **Зображення і a11y.** Усі `<img>` мають `alt`, `width`, `height`, нижні мають `loading="lazy"`. Декоративне лого в шапці й футері це `alt=""` з `aria-hidden`. `:focus-visible`, `prefers-reduced-motion`, aria-label на навігації.
- **Консистентність.** canonical = sitemap = внутрішні посилання (формат `/сторінка.html`). Меню = футер = sitemap, посилань на неіснуючі сторінки немає.

Автоматична перевірка: `python3 tools/qa.py` (останній прогін: 0 помилок). Вона перевіряє h1 і ієрархію, `<main>`, мітки секцій, `<img>`, текст у `div`/`span`, мертві посилання, canonical проти sitemap, JSON-LD проти видимого тексту, довжини title/description.

## Що я свідомо не брав з документа

Усе про рейтинг конкуренток: «незалежний експерт», editorial-бали, Google snapshot, `company-stated`, nofollow-посилання на конкурентів, блок рецензента і схему `Person`. Це сайт однієї компанії, а не рейтинг.

## Перед запуском: що заповнити

1. **Домен.** Зараз скрізь `https://www.example.com`. Або глобальна заміна по всій папці, або `DOMAIN` у `tools/build.py` і запуск `python3 tools/build.py`.
2. **Конфіг у `tools/build.py`.** `CITY`, `PHONE_DISPLAY`/`PHONE_TEL`, `HOURS`, `ADDRESS_TEXT` та `ADDRESS_SCHEMA`, `GEO_*`/`LAT`/`LNG`, `SAME_AS` (профіль Google Business тощо), `GOOGLE_REVIEWS_URL`, `MAPS_URL`, `LICENSE`, `LOCALE`. Після `build.py` місто, телефон, години й адреса підставляються у видимий текст, title, description, схему, а geo-теги з'являються. Поки поле порожнє, відповідні фрагменти просто не виводяться, вигаданих даних у схемі немає.
3. **Жовті плейсхолдери на головній** (їх треба замінити реальними даними руками в `index.html` або в `tools/source-single-page.html` і перезібрати): ціни `[$X–$Y]` та одиниці в трьох картках, дві бокові акції та умови $25 Off, рейтинг `[4.9]`/`[XXX]`, три відгуки, команда (фото, імена, описи), список районів, карта (вставити iframe), номер ліцензії.
4. **Форма.** У `script.js` функція `sendRequest` поки лише імітує відправку, підключіть справжній endpoint.
5. **Розстрочка.** Блоки «Payment plans» і відповідь у FAQ описують оплату частинами. Залиште їх лише якщо вона у вас справді є.

## Чого в схемі немає навмисно

`aggregateRating` і `Review` не додані: поки немає справжніх відгуків, це порушення правил Google про розмітку. Додавайте їх лише з реальними даними й видимими на сторінці відгуками.

З сторінки екстреної допомоги прибрано два питання FAQ («як швидко приїдете», «чи дорожчий екстрений виклик»): відповіді потребують ваших фактів. Додайте їх, коли знатимете політику, і в `build.py` вони потраплять у схему автоматично. Розділи «Our story» і «Join the team» теж прибрані до появи реального тексту.

`.htaccess` працює на Apache. Для Nginx, Netlify чи Cloudflare Pages ті самі правила (стиснення, кеш, заголовки, 404) налаштовуються інакше.
