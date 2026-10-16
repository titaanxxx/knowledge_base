import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
import os


def generate_qr(url: str, filename: str, fill_color=(47, 111, 237), back_color=(11, 17, 32)):
    """
    Генерирует стилизованный QR-код под тёмную тему проекта.

    :param url: Ссылка, которую кодируем
    :param filename: Имя выходного файла (без расширения)
    :param fill_color: Цвет модулей QR-кода (RGB)
    :param back_color: Цвет фона (RGB)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Максимальная коррекция ошибок
        box_size=12,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Создаём папку для QR-кодов
    os.makedirs('docs/qr', exist_ok=True)

    # Генерируем стилизованный QR-код с градиентом
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask(
            center_color=fill_color,
            edge_color=(78, 205, 196),  # Бирюзовый акцент из палитры проекта
            back_color=back_color
        )
    )

    filepath = f'docs/qr/{filename}.png'
    img.save(filepath)
    print(f"✅ QR-код сохранён: {filepath}")
    print(f"   Ссылка: {url}")


if __name__ == '__main__':
    # GitHub
    generate_qr(
        url='https://github.com/titaanxx/knowledge-base',
        filename='github',
        fill_color=(47, 111, 237),  # Синий из палитры
        back_color=(11, 17, 32)  # Тёмный фон из палитры
    )

    # GitVerse
    generate_qr(
        url='https://gitverse.ru/titanxx/knowledge-base',
        filename='gitverse',
        fill_color=(78, 205, 196),  # Бирюзовый акцент
        back_color=(11, 17, 32)
    )

    # Локальный сервер (для демо на защите)
    generate_qr(
        url='http://127.0.0.1:5000',
        filename='localhost',
        fill_color=(255, 255, 255),  # Белый для контраста
        back_color=(11, 17, 32)
    )

    print("\n🎉 Все QR-коды успешно сгенерированы!")