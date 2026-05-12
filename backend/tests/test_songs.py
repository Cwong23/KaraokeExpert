def test_no_auth_song(client):
    response = client.post('/songs/create_upload')

    assert response.status_code == 401


def test_song_upload_route(client, auth_headers):
    response = client.post('/songs/create_upload', headers=auth_headers)

    assert response.status_code == 200
