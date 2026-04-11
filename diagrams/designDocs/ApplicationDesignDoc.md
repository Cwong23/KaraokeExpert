## Karaoke Expert


### Design Diagram
![](../application_diagram.png)

### Design Explanation
#### Client
Write later

#### Gateway
The gateway layer acts as an abstraction between the client and the backend. It handles REST API requests from the client and handles routing and load balancing to a backend container.

#### Backend
The backend receives routed API requests from the gateway. The main type of request we would recieve is a song upload request. Ultimately, a user should be able to upload a song, and end up with only an instrumental version. 

The client will initiate a multipart upload of a song where it starts with a create request. The backend will create a key/value to store the song prediction status in Redis. The client will upload 30 second chunks in requests that the backend will move to a queue.

The queue will be read by a worker. When the worker is done processing a song, it will notify the backend. The backend will put the song together in the object storage, and create a reference to it in the user database. Finally, the key/value will be deleted in Redis. 

For a user to access a song, the client will make a request to the backend. The backend will reference the database and call the object store to make a temporary URL for the frontend to use.


#### Worker
The worker has been decoupled from the backend to make it separately scalable. The worker reads from the queue and calls its ML model to convert the mix spectrogram into a instrumental spectrogram. The worker then uploads the clip into an object store and updates song status in Redis. Finally, it notifies the backend to that an entire song has been uploaded.


## Questions/Comments

how does the worker notify the backend? Does it use something like SNS?

I don't think the worker needs access to the backend, so this will need to change.

The backend should have an arrow pointing to object storage.

