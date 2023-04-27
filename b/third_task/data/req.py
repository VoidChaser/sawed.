from requests import get, post



print(post('http://localhost:5000/api/posts',
           json={'title': 'Заголовок',
                 'text': 'Текст новости',
                 'post_creator_id': 1,
                 'is_private': 0}).json())