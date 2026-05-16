### API Design
This file contains the high level overview of how APIs are to be used and called. For examples and more indepth documentation, look at the `.yml` files in this directory.

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


#### CreateMultipartUpload

`POST /song/create_upload`

Request
~~~
song_name: str
~~~

Response
~~~
upload_id: str
song_id: str
~~~

#### UploadPart

`POST /song/upload_part`

Request
~~~
upload_id: str
part_numer: int
song_clip: str (binary)
~~~


#### AbortMultipartUpload

`DELETE /song/abort_upload`

Request
~~~
upload_id: str
~~~
