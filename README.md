# Hashtag AI — Instagram Reels uchun Telegram bot + iPhone uslubidagi kabinet

Bot **aiogram 3** da, kabinet (Telegram Web App) esa oddiy HTML/CSS/JS da yozilgan (build kerak emas).
Bir jarayon ikkalasini ham ishga tushiradi: Telegram bot (polling) va Web App serveri (aiohttp).

**Kabinetda faqat 3 bo‘lim:** Hashtag yuklash · Bio yuklash · History.
**Telegram chatida:** /start, majburiy obuna, 16 yo‘nalish, 7 kunlik TOP, AI generator, video analiz, admin, yordam.

## ⚠️ Halol cheklovlar (o‘qing)
1. **Instagram istalgan URL/username uchun ma’lumot bermaydi.** Bot scraping qilmaydi, faqat rasmiy Meta API ishlatadi.
2. **Reels caption (kabinet):** `INSTAGRAM_OEMBED_TOKEN` (Meta oEmbed Read) yoki o‘zingizning Business/Creator akkauntingiz Graph API si orqali. oEmbed ba’zi videolar uchun caption qaytarmasligi mumkin — shunda aniq xato ko‘rsatiladi, soxta natija yaratilmaydi.
3. **Bio:** faqat Graph API `business_discovery` orqali — **Business/Creator** akkauntlar bio si olinadi. Shaxsiy profillar olinmaydi.
4. **TOP videolar:** Graph API `ig_hashtag_search` (`top_media`/`recent_media`). Cheklovlar: **7 kunda 30 ta noyob hashtag**, **ko‘rishlar soni berilmaydi** (faqat layk/izoh). Shuning uchun reyting **layklar bo‘yicha** va "Tekshirilgan videolar orasidagi TOP-3" deb belgilanadi. Sana filtri aniq 7×24 soat.
5. **AI generator:** `GEMINI_API_KEY` bo‘lmasa yoki xizmat ishlamasa, oddiy lokal generator ishlaydi. Har doim "AI tomonidan yaratilgan tavsiya" deb belgilanadi, rekka chiqish kafolati berilmaydi. Gemini bepul darajasining kunlik/daqiqalik limitlari bor ([aistudio.google.com](https://aistudio.google.com/apikey)).
6. **Video analiz:** Telegram bot API orqali 20 MB gacha video yuklab olinadi. Baho evristik taxmin.

## 1. O‘rnatish (Windows)
Python 3.12 o‘rnating (python.org, "Add to PATH" ni belgilang). **FFmpeg** (ixtiyoriy, lekin tavsiya: audio/FPS aniqligi uchun): `winget install Gyan.FFmpeg`.

Loyiha papkasida (`hashtag_ai`) **PowerShell** oching:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

## 2. `.env` ni to‘ldirish
| Kalit | Nima |
|---|---|
| `BOT_TOKEN` | @BotFather dan olingan token |
| `ADMIN_IDS` | Sizning Telegram ID (masalan @userinfobot dan), vergul bilan ko‘p |
| `WEBAPP_URL` | Kabinetning **HTTPS** manzili (3-bo‘lim) |
| `INSTAGRAM_*` | 5-bo‘lim |
| `GEMINI_API_KEY` | ixtiyoriy |

## 3. Testlar va ishga tushirish
```powershell
python -m pytest        # 26 ta test o‘tishi kerak
python -m bot.main      # bot + Web App serveri (port 8080)
```
SQLite jadvallari avtomatik yaratiladi (`data/hashtag_ai.db`).

## 4. Web App uchun HTTPS
Telegram faqat HTTPS ni qabul qiladi.
- **Lokal sinov:** ikkinchi PowerShell oynasida `ngrok http 8080` (yoki `cloudflared tunnel --url http://localhost:8080`) — chiqqan `https://...` manzilni `.env` dagi `WEBAPP_URL` ga yozing va botni qayta ishga tushiring.
- **Doimiy:** GitHub + Render (Web Service). Build: `pip install -r requirements.txt`, Start: `python -m bot.main`. Render `PORT` ni o‘zi beradi (kod uni o‘qiydi). `WEBAPP_URL` = Render manzili. Bepul Render uxlab qoladi; SQLite fayli esa qayta deploydan o‘chadi (doimiy disk yoki boshqa hosting kerak).
- @BotFather → `/mybots` → botingiz → **Bot Settings → Menu Button** orqali ham shu URL ni qo‘yish mumkin (ixtiyoriy; bot o‘zi ham "Kabinetni ochish" tugmasini yuboradi).

## 5. Majburiy obuna
Botni **@o11abu kanaliga admin qiling** (aks holda `getChatMember` ishlamaydi). Kanal `.env` da: `REQUIRED_CHANNEL=@o11abu`. Obuna bo‘lmaguncha bot ham, kabinet API si ham bloklanadi. Xato bo‘lsa logga yoziladi va foydalanuvchiga tushunarli xabar chiqadi.

## 6. Instagram rasmiy sozlash
1. Instagram akkauntingizni **Business/Creator** ga o‘tkazing va Facebook Sahifaga ulang.
2. [developers.facebook.com](https://developers.facebook.com) da ilova yarating; **Instagram Graph API** va **oEmbed** ni qo‘shing.
3. Ruxsatlar: `instagram_basic`, `instagram_manage_insights` (kerak bo‘lsa), **Instagram Public Content Access** (hashtag qidiruv uchun, Meta ko‘rib chiqadi — App Review kerak).
4. Uzoq muddatli (long-lived) access token oling → `INSTAGRAM_ACCESS_TOKEN`; Instagram akkaunt ID → `INSTAGRAM_USER_ID`.
5. oEmbed uchun `APP_ID|CLIENT_TOKEN` → `INSTAGRAM_OEMBED_TOKEN`.
Tokenlar faqat serverda, `.env` da turadi; frontendga chiqmaydi va logda yashiriladi.

## 7. Xavfsizlik
Web App so‘rovlari Telegram `initData` imzosi (HMAC) bilan tekshiriladi; History faqat shu foydalanuvchiga tegishli; rate-limit, timeout, URL/username validatsiyasi, video hajmi tekshiruvi bor. Instagram paroli so‘ralmaydi.

## 8. Tuzilma
```
bot/            main.py, config.py, loader.py, middlewares.py, webapi.py
  handlers/     start, subscription, hashtag(TOP), generator, video_analysis, bio, history, admin
  keyboards/    inline, reply, webapp
  services/     instagram_api, trend_analyzer, hashtag_generator, caption_analyzer,
                video_analyzer, bio_service, subscription_service, directions
  database/     models(SQL), session, repository
  utils/        logger, validators, text_formatter, time_utils, ratelimit
webapp/         index.html, src/{main,api}.js, styles.css, pages/{hashtag,bio,history}.js, components/
tests/          5 ta test fayli (26 test)
```
