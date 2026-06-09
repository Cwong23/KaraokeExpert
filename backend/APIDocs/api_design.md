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

#### GetSong

`GET /song`

Request
~~~
song_name: str
~~~

Response
~~~
url: str
song_id: str
~~~


#### DeleteSong

`DELETE /song/delete`

Request
~~~
song_id: str
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
