### API Design
This file contains the high level overview of how APIs are to be used and called.

#### Example
`GET /path/to/api`

Request
~~~
example param: str
example param: list[str]
~~~

Response
~~~
example param: int
~~~


#### CreateUpload

`POST /song/create_upload`

Request
~~~
song_name: str
~~~

Response
~~~
url: str
song_id: str
~~~

#### ProcessSong

`PUT /song/process_song`

Request
~~~
song_id: str
~~~

#### GetSongStatus

`GET /<song_id>/status`


Response
~~~
status: str
~~~

#### GetCompletedSongs

`GET /get_completed_songs`


Response
~~~
song_ids: [str]
~~~

#### GetProcessingSongs

`GET /get_processing_songs`


Response
~~~
song_ids: [str]
~~~

#### GetSongObjects

`GET /<song_id>/get_song_objects`


Response
~~~
urls: [str]
~~~

#### GetSongData

`GET /<song_id>/get_song_data`

Request
~~~
song_name: str
~~~

Response
~~~
song: dict
~~~


#### Register
`POST /auth/register`

Request
~~~
email: str
password: str
~~~

#### Login
`POST /auth/login`

Request
~~~
email: str
password: str
~~~

Response
~~~
token: str
~~~
