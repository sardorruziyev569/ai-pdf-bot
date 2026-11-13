import os
import re
import asyncio
import numpy as np
from io import BytesIO
from PIL import Image, ImageEnhance
from fpdf import FPDF
from aiohttp import web
from rapidocr_onnxruntime import RapidOCR
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = "9091356459:AAGLP3Uj64zx97vLxSFb2nuz65YKk6cQpX0"
ADMIN_USERNAME = "Sardor_Ruziyevv"

session = AiohttpSession(timeout=60)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

ocr_engine = RapidOCR()
foydalanuvchi_rejimi = {}
yigilgan_rasmlar = {}

def menyu_olish(user_id: int) -> ReplyKeyboardMarkup:
    rasm_soni = len(yigilgan_rasmlar.get(user_id, []))
    tugmalar = []
    if rasm_soni > 0:
        tugmalar.append([KeyboardButton(text=f"✅ Rasmlardan PDF yasash ({rasm_soni} ta)"), KeyboardButton(text="🗑 Rasmlarni o‘chirish")])
    tugmalar.append([KeyboardButton(text="📄 Asl holicha PDF qilish"), KeyboardButton(text="🆕 Yangi alifboda PDF qilish")])
    tugmalar.append([KeyboardButton(text="🖼 Rasmlarni PDF ga birlashtirish")])
    tugmalar.append([KeyboardButton(text="ℹ️ Bot haqida"), KeyboardButton(text="👨‍💻 Admin bilan bog'lanish")])
    return ReplyKeyboardMarkup(keyboard=tugmalar, resize_keyboard=True)

@dp.message(CommandStart())
async def start_buyrugi(message: types.Message):
    uid = message.from_user.id
    foydalanuvchi_rejimi[uid] = "yangi"
    yigilgan_rasmlar[uid] = []
    salom_matni = (
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Men rasmlardagi matnni o‘qib <b>PDF</b> qiluvchi hamda bir nechta rasmlarni "
        "<b>1 ta umumiy PDF</b> faylga birlashtiruvchi botman.\n\n"
        "👇 Kerakli bo‘limni tanlang:\n\n"
        f"👨‍💻 <i>Bu bot <a href='https://t.me{ADMIN_USERNAME}'><b>Ro‘ziyev Sardor</b></a> tomonidan yaratilgan.</i>"
    )
    await message.answer(salom_matni, parse_mode="HTML", reply_markup=menyu_olish(uid), disable_web_page_preview=True)

@dp.message(F.text.contains("Asl holicha PDF"))
async def asl_rejim_tanlash(message: types.Message):
    uid = message.from_user.id
    foydalanuvchi_rejimi[uid] = "asl"
    yigilgan_rasmlar[uid] = []
    await message.answer("📄 <b>Asl holicha PDF qilish</b> rejimi tanlandi! Rasm yuboring.", parse_mode="HTML", reply_markup=menyu_olish(uid))

@dp.message(F.text.contains("Yangi alifboda PDF"))
async def yangi_rejim_tanlash(message: types.Message):
    uid = message.from_user.id
    foydalanuvchi_rejimi[uid] = "yangi"
    yigilgan_rasmlar[uid] = []
    await message.answer("🆕 <b>Yangi alifboda PDF (Ö, Ğ, Ş, Ç)</b> rejimi tanlandi! Rasm yuboring.", parse_mode="HTML", reply_markup=menyu_olish(uid))

@dp.message(F.text.contains("Rasmlarni PDF ga birlashtirish"))
async def rasm_albom_tanlash(message: types.Message):
    uid = message.from_user.id
    foydalanuvchi_rejimi[uid] = "albom"
    yigilgan_rasmlar[uid] = []
    await message.answer(
        "🖼 <b>Rasmlarni 1 ta PDF ga birlashtirish</b> rejimi yoqildi!\n\n"
        "5–6 ta (yoki istalgancha) rasmlaringizni ketma-ket yuboring. "
        "Barchasini yuborgach, pastdagi <b>«✅ Rasmlardan PDF yasash»</b> tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=menyu_olish(uid)
    )

@dp.message(F.text == "🗑 Rasmlarni o‘chirish")
async def rasmlarni_tozalash(message: types.Message):
    uid = message.from_user.id
    for yol in yigilgan_rasmlar.get(uid, []):
        if os.path.exists(yol):
            os.remove(yol)
    yigilgan_rasmlar[uid] = []
    await message.answer("🗑 Yig‘ilgan rasmlar tozalandi.", reply_markup=menyu_olish(uid))

@dp.message(F.text.contains("Bot haqida"))
async def bot_haqida(message: types.Message):
    matn = (
        "🤖 <b>Bot imkoniyatlari:</b>\n\n"
        "• Ikki ustunli test va hujjatlarning asl ko‘rinishini saqlab matnli PDF qiladi.\n"
        "• Yangi o‘zbek alifbosi (Ö, Ğ, Ş, Ç) ga avtomatik o‘giradi.\n"
        "• Bir nechta rasmlarni sifatini buzmasdan <b>1 ta umumiy PDF</b> faylga birlashtiradi.\n\n"
        f"👨‍💻 <i>Bu bot <a href='https://t.me{ADMIN_USERNAME}'><b>Ro‘ziyev Sardor</b></a> tomonidan yaratilgan.</i>"
    )
    await message.answer(matn, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.text.contains("Admin bilan"))
async def admin_bilan_boglanish(message: types.Message):
    tugma = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✉️ Adminga yozish", url=f"https://t.me{ADMIN_USERNAME}")]])
    await message.answer(f"👤 <b>Admin:</b> <a href='https://t.me{ADMIN_USERNAME}'><b>Ro‘ziyev Sardor</b></a>\n🔗 <b>Telegram:</b> @{ADMIN_USERNAME}", parse_mode="HTML", reply_markup=tugma, disable_web_page_preview=True)
def yangi_alifboga_otkazish(matn: str) -> str:
    matn = re.sub(r"([Ss])['‘’`ʻʼ]([Hh])", r"\1\2_TEMP_", matn)
    matn = re.sub(r"O['‘’`ʻʼ]", "Ö", matn)
    matn = re.sub(r"o['‘’`ʻʼ]", "ö", matn)
    matn = re.sub(r"G['‘’`ʻʼ]", "Ğ", matn)
    matn = re.sub(r"g['‘’`ʻʼ]", "ğ", matn)
    matn = matn.replace("SH", "Ş").replace("Sh", "Ş").replace("sh", "ş")
    matn = matn.replace("CH", "Ç").replace("Ch", "Ç").replace("ch", "ç")
    return matn.replace("_TEMP_", "")

def matnni_tozalash(matn: str, yangi_alifbo: bool = False) -> str:
    if yangi_alifbo:
        matn = yangi_alifboga_otkazish(matn)
    toza = re.sub(r'[^\w\s\.,;:!\?\-\(\)\[\]\"\'«»—–/\\+=%№@#&*<>\n\r‘’“”ÖöĞğŞşÇçўқғҳЎҚҒҲёЁ]', '', matn)
    toza = re.sub(r'([,\.;:!\?])([^\s\d\n])', r'\1 \2', toza)
    return toza.strip()

def matndan_pdf_yaratish(ustunlar: list[str], fayl_nomi: str, yangi_alifbo: bool = False):
    if len(ustunlar) == 2:
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        pdf.add_font("ArialUZ", "", "arial.ttf")
        pdf.set_font("ArialUZ", size=11)
        pdf.line(148.5, 10, 148.5, 200)
        chap_matn = matnni_tozalash(ustunlar[0], yangi_alifbo)
        ong_matn = matnni_tozalash(ustunlar[1], yangi_alifbo)
        pdf.set_xy(10, 12)
        pdf.multi_cell(132, 7, text=chap_matn)
        pdf.set_xy(154, 12)
        pdf.multi_cell(132, 7, text=ong_matn)
    else:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.add_font("ArialUZ", "", "arial.ttf")
        pdf.set_font("ArialUZ", size=12)
        toza = matnni_tozalash(ustunlar[0], yangi_alifbo)
        pdf.multi_cell(0, 8, text=toza if toza else "Matn topilmadi.")
    pdf.output(fayl_nomi)

def qatorlarni_tartiblash(elementlar: list) -> str:
    if not elementlar:
        return ""
    elementlar.sort(key=lambda e: (round(e[0] / 12), e[1]))
    qatorlar, joriy, oldingi_y = [], [], None
    for y, x, matn in elementlar:
        if oldingi_y is None or abs(y - oldingi_y) < 18:
            joriy.append(matn)
        else:
            qatorlar.append(" ".join(joriy))
            joriy = [matn]
        oldingi_y = y
    if joriy:
        qatorlar.append(" ".join(joriy))
    return "\n".join(qatorlar)

def rasmni_oqish(rasm: Image.Image) -> list[str]:
    if rasm.mode != "RGB":
        rasm = rasm.convert("RGB")
    w, h = rasm.size
    if w < 1800:
        rasm = rasm.resize((1800, int(h * 1800 / w)), Image.Resampling.LANCZOS)
    rasm = ImageEnhance.Contrast(rasm).enhance(1.3)
    rasm = ImageEnhance.Sharpness(rasm).enhance(1.5)
    yangi_w, _ = rasm.size
    natija, _ = ocr_engine(np.array(rasm))
    if not natija:
        raise Exception("Rasmdan matn topilmadi")
    chap_el, ong_el = [], []
    for item in natija:
        box, matn = item[0], item[1]
        if isinstance(matn, str):
            x_markaz = (box[0][0] + box[2][0]) / 2
            y_markaz = (box[0][1] + box[2][1]) / 2
            if x_markaz < (yangi_w * 0.48):
                chap_el.append((y_markaz, x_markaz, matn))
            else:
                ong_el.append((y_markaz, x_markaz, matn))
    if len(chap_el) >= 2 and len(ong_el) >= 2:
        return [qatorlarni_tartiblash(chap_el), qatorlarni_tartiblash(ong_el)]
    return [qatorlarni_tartiblash(chap_el + ong_el)]

def rasmlarni_bitta_pdf_qilish(rasm_yollari: list[str], pdf_nomi: str):
    ochilgan_rasmlar = []
    for yol in rasm_yollari:
        img = Image.open(yol)
        if img.mode != "RGB":
            img = img.convert("RGB")
        ochilgan_rasmlar.append(img)
    birinchi = ochilgan_rasmlar[0]
    qolganlari = ochilgan_rasmlar[1:]
    birinchi.save(pdf_nomi, save_all=True, append_images=qolganlari)
    for img in ochilgan_rasmlar:
        img.close()

@dp.message(F.text.startswith("✅ Rasmlardan PDF yasash"))
async def albom_pdf_yaratish(message: types.Message):
    uid = message.from_user.id
    yollar = yigilgan_rasmlar.get(uid, [])
    if not yollar:
        await message.answer("⚠️ Hali rasm yubormadingiz!")
        return
    kutish = await message.answer(f"⏳ {len(yollar)} ta rasm bitta PDF faylga birlashtirilmoqda...")
    pdf_nomi = f"albom_{uid}_{message.message_id}.pdf"
    try:
        await asyncio.to_thread(rasmlarni_bitta_pdf_qilish, yollar, pdf_nomi)
        tayyor = types.FSInputFile(pdf_nomi)
        await message.answer_document(tayyor, caption=f"✅ {len(yollar)} ta rasmdan iborat PDF tayyor!\n👨‍💻 Yaratuvchi: Ro‘ziyev Sardor (@{ADMIN_USERNAME})")
        await kutish.delete()
    except Exception as e:
        await kutish.edit_text(f"❌ Xatolik: {e}")
    finally:
        for yol in yollar:
            if os.path.exists(yol):
                os.remove(yol)
        yigilgan_rasmlar[uid] = []
        if os.path.exists(pdf_nomi):
            os.remove(pdf_nomi)
        await message.answer("🖼 Yana rasmlar yuborishingiz yoki boshqa bo‘limni tanlashingiz mumkin.", reply_markup=menyu_olish(uid))

async def rasmni_qayta_ishlash(message: types.Message, file_id: str):
    uid = message.from_user.id
    rejim = foydalanuvchi_rejimi.get(uid, "yangi")
    if rejim == "albom":
        yigilgan_rasmlar.setdefault(uid, [])
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path, timeout=60)
        vaqtincha_rasm = f"temp_{uid}_{message.message_id}.jpg"
        with open(vaqtincha_rasm, "wb") as f:
            f.write(downloaded_file.read())
        yigilgan_rasmlar[uid].append(vaqtincha_rasm)
        soni = len(yigilgan_rasmlar[uid])
        await message.answer(f"🖼 <b>{soni}-rasm</b> qo‘shildi! Yana rasm yuboring yoki pastdagi <b>«✅ Rasmlardan PDF yasash»</b> tugmasini bosing.", parse_mode="HTML", reply_markup=menyu_olish(uid))
        return
    yangi_mi = (rejim == "yangi")
    rejim_nomi = "Yangi alifbo (Ö, Ğ, Ş, Ç)" if yangi_mi else "Asl holicha"
    kutish_xabari = await message.answer(f"⏳ Rasm ko‘rinishi saqlangan holda PDF tayyorlanmoqda ({rejim_nomi})...")
    pdf_nomi = f"hujjat_{uid}_{message.message_id}.pdf"
    try:
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path, timeout=60)
        rasm = Image.open(BytesIO(downloaded_file.read()))
        ustunlar = await asyncio.to_thread(rasmni_oqish, rasm)
        matndan_pdf_yaratish(ustunlar, pdf_nomi, yangi_alifbo=yangi_mi)
        tayyor_fayl = types.FSInputFile(pdf_nomi)
        await message.answer_document(tayyor_fayl, caption=f"✅ Hujjat asl ko‘rinishida tayyor! ({rejim_nomi})\n👨‍💻 Yaratuvchi: Ro‘ziyev Sardor (@{ADMIN_USERNAME})")
        await kutish_xabari.delete()
    except Exception as e:
        await kutish_xabari.edit_text(f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(pdf_nomi):
            os.remove(pdf_nomi)

@dp.message(F.photo)
async def foto_qabul_qilish(message: types.Message):
    await rasmni_qayta_ishlash(message, message.photo[-1].file_id)

@dp.message(F.document)
async def fayl_qabul_qilish(message: types.Message):
    if message.document.mime_type and message.document.mime_type.startswith("image/"):
        await rasmni_qayta_ishlash(message, message.document.file_id)
    else:
        await message.answer("⚠️ Iltimos, faqat rasm (JPG, PNG) yuboring!")

async def health_check(request):
    return web.Response(text="Bot 24/7 ishlayapti!")

async def main():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Bot {port}-portda 24/7 rejimida ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
