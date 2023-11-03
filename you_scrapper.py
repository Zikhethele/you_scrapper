import requests
from googleapiclient.discovery import build
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import glob

# import with_attachment

# Replace 'YOUR_API_KEY' with your actual API key
API_KEY = ''
youtube = build('youtube', 'v3', developerKey=API_KEY)

smtp_port = 587
smtp_server = "smtp.gmail.com"
# Replace 'pawd' with your actual google app password
pswd = ""
email_from = "zikhethelegumede@gmail.com"

def send_emails(email_list,name):
    subject = "Youtube channel datasets for " + name
    pwd = os.getcwd()
    directory = pwd + '/' + name
    print(directory)
    for person in email_list:
        body = f"""
        Hi 
        
        See datasets for the requested youtube channel attached
        """

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = person
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # filename = ["CliffCentralcom.csv","CliffCentralcom_statistics.csv","CliffCentralcom_Monthly_stats.csv"]
        filename = glob.glob(channel_name + '*.csv')
        # filename = glob.glob(directory + '/' +'*.csv')
        print(filename)
        for item in filename:
            # item = os.path.basename(item)
            # os.chdir('/' + id)
            print('Attachment',item)
            attachment = open(item, 'rb')

            #Encode
            attachment_package = MIMEBase('application', 'octet-stream')
            attachment_package.set_payload((attachment).read())
            encoders.encode_base64(attachment_package)
            attachment_package.add_header('Content-Disposition',"attachment; filename= " + item)
            msg.attach(attachment_package)

        text = msg.as_string()

        #Connect with server
        print("Connecting to server....")
        TIE_server = smtplib.SMTP(smtp_server,smtp_port)
        TIE_server.starttls()
        TIE_server.login(email_from,pswd)
        print("Succesfully connected to server")
        print()

        print(f"Sending email to : {person}")
        TIE_server.sendmail(email_from,person,text)
        print(f"Email sent to : {person}")
        print()

    TIE_server.quit()

def get_channel_id(channel_name):
    # Initialize the YouTube API client
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # Search for the channel using the channel name
    search_response = youtube.search().list(
        q=channel_name,
        type='channel',
        part='id'
    ).execute()
#     print("Response:", search_response)

    # Get the channel ID from the search result
    if search_response['items'][0]['id']['channelId']:
        channel_id = search_response['items'][0]['id']['channelId']
        print("Channel ID:", channel_id)
        # Get the uploads playlist ID for the channel
        channels_response = youtube.channels().list(
            id=channel_id,
            part='contentDetails'
        ).execute()


    return channel_id

def get_channel_stats(youtube,channel_ids):
    
    all_data = []
    
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_ids
    )    
    response = request.execute()
    
    for item in response['items']:
        
        data = {'channel_name':item['snippet']['title'],
               'subscribers':item['statistics']['subscriberCount'],
               'views':item['statistics']['viewCount'],
               'totalVideos':item['statistics']['videoCount'],
               'PlaylistID':item['contentDetails']['relatedPlaylists']['uploads']}
        
        all_data.append(data)
        df = pd.DataFrame(all_data)
        
    return df

def get_video_ids(youtube,playlistid):
    request = youtube.playlistItems().list(
                part='ContentDetails',
                playlistId = playlistid,
                maxResults = 50)
    response = request.execute()
    
    video_ids = []
    
    for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])
        
    next_page_token = response['nextPageToken']
    more_pages = True
    
    while more_pages:
        
        if next_page_token is None:
            more_pages = False
        else:
            request = youtube.playlistItems().list(
                        part='ContentDetails',
                        playlistId = playlistid,
                        maxResults = 50,
                        pageToken = next_page_token)
            response = request.execute()
            
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
    return video_ids

def get_video_details(youtube,video_ids):
    all_video_stats = []
    for i in range(0,len(video_ids),50):    
        request = youtube.videos().list(
                    part='snippet,statistics',
                    id=','.join(video_ids[i:i+50]))
        response = request.execute()
#         print('Res Item',response['items'])
        for video in response['items']:
            video_stats = dict(Channel = video['snippet']['channelTitle'],
                               Title = video['snippet']['title'],
                              Published_date = video['snippet']['publishedAt'],
                              Views = video['statistics']['viewCount'],
                              Likes = video['statistics']['likeCount'])

            all_video_stats.append(video_stats)
    return all_video_stats

if __name__ == '__main__':
    channel_name = input("Enter the YouTube channel name: ")
    channel_id = get_channel_id(channel_name)

    if channel_id:
        pwd = os.getcwd() 
        
        print(f"Channel ID for '{pwd} {channel_name}': {channel_id}")
        ch_id = get_channel_stats(youtube,channel_id)
        print(ch_id)
        
        for pl_id in ch_id['PlaylistID']:
            for channel_name in ch_id['channel_name']:
                new_dir = pwd + '/' + pl_id
                
                if os.path.exists(new_dir):
                    print('Channel Name: ',channel_name, new_dir)
                else:
                    os.mkdir(new_dir)
                    
                ch_id.to_csv(channel_name + ".csv", sep=",", index=False, encoding="utf-8")

                video_ids = get_video_ids(youtube,pl_id)

                video_details = get_video_details(youtube,video_ids)
                video_data = pd.DataFrame(video_details)   
#                 print(video_data)
                
                video_data['Published_date'] = pd.to_datetime(video_data['Published_date']).dt.date
                video_data['Views'] = pd.to_numeric(video_data['Views'])
                video_data['Likes'] = pd.to_numeric(video_data['Likes'])
                video_data.to_csv(channel_name + ' statistics.csv', sep=",", index=False, encoding="utf-8")

                video_data['Month'] = pd.to_datetime(video_data['Published_date']).dt.strftime('%b')
                sorted_videos = video_data.sort_values(by='Published_date', ascending=True)
                videos_per_month = video_data.groupby('Month', as_index=False).size()
                sort_monthly = videos_per_month.sort_values(by='Month', ascending=True)
                sort_monthly.to_csv(channel_name + " monthly stats.csv",sep=",",index=False, encoding="utf-8")
                print("Sorted Monthly :" ,sort_monthly)

                top10 = video_data.sort_values(by='Views', ascending=False).head(10)
                top10.to_csv(channel_name + ' Top 10 videos' + '.csv',sep=",", index=False, encoding='utf-8')
#                 print(top10)
                fig, ax = plt.subplots(figsize=(8,10))
                bars = plt.barh(top10['Title'],top10['Views'], color='orange')
                ax.spines[['right','top','bottom']].set_visible(False)
                ax.xaxis.set_visible(False)
#                 , fmt='%.1f%%'
                ax.bar_label(bars, padding=-65, color='white', fontsize=12, label_type='edge', fontweight='bold')
                # plt.savefig(new_dir + '/Top_10_' + channel_name + '.png', dpi=300, bbox_inches='tight')
                plt.savefig(channel_name + '.png', dpi=300, bbox_inches='tight')
                # plt.savefig('Top_10_' + channel_name + '.png', dpi=300, bbox_inches='tight')
                # plt.show()
                plt.close()

                rmail = input('Enter email address : ')
                print('Dataset sent to ', rmail)
                send_emails([rmail],channel_name)
                
#                 top10.plot(x='Title',y='Views',kind='bar')
#                 plt.title('Top 10 ' + channel_name + ' Videos')
#                 plt.xlabel('Video Title')
#                 plt.ylabel('Number of Views')
#                 plt.xticks(rotation=45)
#                 plt.yticks(rotation=45)
#                 plt.show()
        print(f"{channel_name}'.")
