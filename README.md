# Karaoke Expert
Authors: [Kyle Lin](https://www.linkedin.com/in/kyle-lin-584235295/) and [Chris Wong](https://www.linkedin.com/in/chrispwong23/)

![](diagrams/upload_page.png)

## Description
Karaoke Expert is a web app where users can upload their own songs and access lyrics and instrumental music to sing over. This project is Chris and Kyle's senior project for their university where they are currently going into their senior year. The idea stemmed from their experience with doing karaoke in their hometown and the limited selection that karaoke places offered. Check out our design docs in the diagrams directory!

Users can upload as many songs as they would like and it takes around 5 minutes for one song to be processed. The application is encouraged to be used with computers with good GPUs because of the AI models that it uses to separate songs and translate speech to text. Due to copyright laws, this application should only be used with copyright free music as downloading copyrighted music is illegal.  

## Installation
Users should have Docker installed. Docker handles the downloading of other services and packages used in this project. First pull the project and enter that directory. Run `docker compose up --build` to create the image. After run `docker compose up -d` to start the container. Users should then be able to access Karaoke Expert through http://localhost:5173/.
