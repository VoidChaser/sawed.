from PIL import Image
import os


def create_miniature(path: str):
    img = Image.open(path)
    size = x, y = img.size
    print(size)
    if x > y:
        new_img = img.resize((x // 3, y // 2))
    elif x < y:
        new_img = img.resize((x // 2, y // 3))
    else:
        new_img = img.resize((x // 3, y // 3))
    new_dir = path.split('/')[0] + '/miniatures'
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
    mini_path = f'{new_dir}/{path.split("/")[-1]}'
    print(mini_path)
    new_img.save(mini_path)

    return mini_path