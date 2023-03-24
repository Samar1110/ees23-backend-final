from datetime import datetime
from django.core.mail import EmailMessage

part1 = """<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mail</title>
    <style>
        #main div {
            margin-left: auto;
            margin-right: auto;
            max-width: 600px;
        }

        #header {
            background-image: linear-gradient(rgb(10, 10, 173), rgb(0, 38, 255));
            color: white;
            align-items: center;
            justify-content: center;
            display: block;
            max-width:100%;
            width: 100%;
            height: 30vw;
            margin: auto;
            overflow:hidden;
        }
        #back{
            font-size: 40px;
            text-align: center;
            padding-top: 10vw;
            font-family: Arial, Helvetica, sans-serif;
        }
        #header img {
            position: absolute;
            width: 97vw;
            max-width:600px;
            height: auto;
            margin: auto;
        }

        #content {
            font-size: 18px;
            font-family: Arial, Helvetica, sans-serif;
            padding-top: 10px;
        }

        #content div{
            width: 100%;
            text-align: center;
            margin: 20px 0px;
            padding: 20px 0px;
        }

        #btn {
            text-decoration: none;
            color: white;
            background-color:  rgb(50, 101, 231);
            text-align: center;
            padding: 10px 20px;
        }

        #footer{
            background-image: linear-gradient(rgb(44, 130, 241),rgb(11, 47, 167));
            color: white;
            text-align: center;
            padding: 4px;
            font-family: Arial, Helvetica, sans-serif;

        }
        #footer p{
            font-size: 15px;
        }
        #footer img{
            border: 3px solid white;
            width: 20px;
            height: 20px;
            border-radius: 8px;
            padding: 8px;
            margin: 8px 8px 0px 8px;
        }
        #links a{
            color: white;
        }
        @media screen and (min-width: 600px){
            #header{
                height: 200px;
            }
            #back{
                font-size: 60px;
                padding-top: 70px;
            }
        }
        @media screen and (max-width: 413px) {
            #content {
                font-size: 4.5vw;
            }
            #footer p{
                font-size: 10px;
            }
            #footer img{
                width: 16px;
                height: 16px;
                border: 2px solid white;
                border-radius: 5px;
                padding: 1vw;
            }
            #btn{
                padding: 7px 10px;
            }
        }
    </style>
</head>

<body>
    <div id="main">
        <div id="header">
            <img src="https://drive.google.com/uc?export=view&id=1ySrfx7AqoICXgJfqCMd_HqGxKuePozT8" alt="UDYAM">
            <div id="back">UDYAM'22</div>
        </div>
        <div id="content">
            <p>
                Hi """

part2 = """!</b><br>"""
part3 = """</p>
            <div>
                <a id="btn" href='"""
part4 = """'>"""
part5 = (
    """</a>
            </div>
            <p>Team Udyam</p>
        </div>
        <div id="footer">
            <div id="links">
                <a href="https://www.linkedin.com/company/udyam">
                <img src="https://drive.google.com/uc?export=view&id=1TqS0rYellXxX2TS1PNOOGzFfqp9BkyHS" alt="in"></a>
                <a href="https://www.facebook.com/udyamfest/">
                <img src="https://drive.google.com/uc?export=view&id=1gZLFke7rkGTiv8y565QpRQtfuchLinFz" alt="fs"></a>
                <a href="https://instagram.com/udyam_iit_bhu?utm_medium=copy_link">
                <img src="https://drive.google.com/uc?export=view&id=1MjFgADBmTdic_AMJB876w3UJOEUDlXep" alt="&#9677;"></a>
                <a href=" https://youtube.com/channel/UC8wlztNbDIu38rfQ1HChSIg">
                <img src="https://drive.google.com/uc?export=view&id=1K3RJUu8u6bM_Vm9QeWF7j-dX-PXINSVI" alt="&#9658;"></a>
            </div>
            <p>
                &copy; 2022 Udyam All rights reserved.
            </p>
        </div>
    </div>
    <span style="color: #FFF; display: none; font-size: 8px;">"""
    + str(datetime.now())
    + """</span>
</body>
</html>"""
)


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data["email_subject"], body=data["email_body"], to=data["to_mail"]
        )
        email.content_subtype = "html"
        email.send()
