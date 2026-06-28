## Karaoke Expert


### Design Diagram
![](../application_diagram.png)

### Design Explanation
#### Frontend
The frontend is built with React and Vite. Authentication is handled through a login/sign up page, and on successful authentication, the user is taken to the home page, which displays their uploaded songs and an option to upload a new one. Once the user clicks "upload song", the website navigates to the song preview page where they can view their chosen song's lyrics once the backend returns the lyrics and instrumental. 

#### Backend
The backend handles the authenticating and account creation through the login, logout, and register user functionalities. It creates a new entry for a user in the user MongoDB table. When a user wants to upload a song, the frontend uses the `CreateUpload` API which creates an entry in the songs MongoDB table and returns a presigned URL to upload a song to MinIO. The frontend then calls the `ProcessSong` API that creates a new entry in Redis, for state tracking, and publishes a message to Apache Kafka. When the frontend needs song objects, it calls the `GetSongObjects` API which responds with presigned URLs for the lyrics.json and instrumental.wav. To get completed and processing songs, the `GetCompletedSongs` and `GetProcessing` songs that query MongoDB to return song ids with that status. The `GetSongData` API gets a song entry from MongoDB given the song ID.


#### Worker
The worker has been decoupled from the backend to make it separately scalable. The worker consumes from Apache Kafka and processes the message. It gets the original.wav from MinIO and uses Torch Audio to separate the instrumental from the vocals. It uploads both to MinIO and passes the vocal audio into Whisperx which determines the text from the speech. It compiles this into the lyrics.json and uploads this to MinIO. The music separation model that I (Chris Wong) created was not good enough to convert the vocals into lyrics, so we switched to Torch Audio.
