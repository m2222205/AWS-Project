firstly i downloaded the kaggle csv file from kaggle like sales secondly i create RdS database using postgrase sql like we did in previous classes than i checked ec2 instance 
like inbound rules i changes port to 5432 
3 step is i connect and open postgrase sql with my password and username and endpoint and connect it than i import csv data like from kaggle created table 
then i create s3 bucket in aws give name to this bucket added bucket policy rule than uploaded my Html and Css and js file i go to ec2 instance allow 80 and 22 ports and make all
ssh connection i use endpoint and public ip thank i intalled flask and postgrase client
 run this command in terminal sudo apt update
sudo apt install python3-pip
pip3 install flask psycopg2-binary
i created python file app.py and paste my code and make connection to database DBeveaver postgrase sql i put end-point and my db name username and password and made add and delete functions
i make the port 0 0 0 0 port = 80
than i run flask app 
run this command sudo python3 app.py
that all all my project worked correctly 
