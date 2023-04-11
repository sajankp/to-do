To run this Application 
1. Built the docker image using `sudo docker build -t todoimage .`
2. Run the container based on the image using `sudo docker run -d --name todocontainer -p 80:80 todoimage`