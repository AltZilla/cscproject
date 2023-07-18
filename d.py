import requests

# https://open.spotify.com/track/44ut2KJnt0HQMnUaMlDv9W
headers = {
    'origin': 'https://spotifydown.com',
    'referer': 'https://spotifydown.com/'
}

link = f'https://api.spotifydown.com/download/44ut2KJnt0HQMnUaMlDv9W'

response = requests.get(url = link, headers=headers )
print("Download Link: ", response.json()['link'])
