from flask import Flask, request, render_template_string, redirect, url_for
import requests
import time

app = Flask(__name__)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# ================== HTML ==================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X | Multi ID Loader</title>
<style>
:root{
  --max-w:700px;
  --card-h:900px;
}
body{
  margin:0;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  font-family:Poppins, sans-serif;
  background:linear-gradient(to bottom left, #ff0000, #800080);
}
.container{
  max-width:var(--max-w);
  height:var(--card-h);
  width:100%;
  background:rgba(0,0,0,0.65);
  border-radius:20px;
  box-shadow:0 15px 40px rgba(0,0,0,0.6);
  padding:30px;
  display:flex;
  flex-direction:column;
  justify-content:flex-start;
}
h1{
  text-align:center;
  font-size:2.5rem;
  margin:0;
  margin-bottom:10px;
  color:#fff;
  text-shadow:0 0 10px rgba(255,255,255,0.4);
}
h2{
  text-align:center;
  font-size:1.2rem;
  margin:0 0 30px;
  color:#ffcccc;
  font-weight:400;
}
label{
  color:#fff;
  font-weight:600;
  margin-bottom:5px;
  display:block;
}
.form-control{
  width:100%;
  padding:12px 15px;
  margin-bottom:15px;
  border-radius:12px;
  border:none;
  outline:none;
  font-size:1rem;
  background:rgba(255,255,255,0.1);
  color:white;
  box-shadow:0 0 5px rgba(255,255,255,0.2) inset;
}
.form-control::placeholder{
  color:#ddd;
}
.btn-submit{
  width:100%;
  padding:14px;
  border:none;
  border-radius:14px;
  font-size:1.2rem;
  font-weight:bold;
  cursor:pointer;
  background:linear-gradient(90deg,#ff0000,#800080);
  color:white;
  margin-top:10px;
  transition:0.3s ease-in-out;
}
.btn-submit:hover{
  transform:scale(1.05);
  box-shadow:0 0 15px rgba(255,255,255,0.3);
}
footer{
  text-align:center;
  color:#fff;
  margin-top:auto;
  font-size:0.9rem;
  opacity:0.8;
}
</style>
</head>
<body>
<div class="container">
  <h1>HENRY-X</h1>
  <h2>Multi ID Offline Loader</h2>
  <form action="/" method="post" enctype="multipart/form-data">
    <label for="threadId">Enter Convo ID:</label>
    <input type="text" class="form-control" id="threadId" name="threadId" placeholder="Your Thread/Convo ID" required>

    <label for="txtFile">Select Your Token File:</label>
    <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>

    <label for="messagesFile">Select Your NP File:</label>
    <input type="file" class="form-control" id="messagesFile" name="messagesFile" accept=".txt" required>

    <label for="kidx">Enter Hater Name:</label>
    <input type="text" class="form-control" id="kidx" name="kidx" placeholder="Enter Hater/Username" required>

    <label for="time">Speed in Seconds:</label>
    <input type="number" class="form-control" id="time" name="time" value="60" required>

    <button type="submit" class="btn-submit">SUBMIT YOUR DETAILS</button>
  </form>
  <footer>Made By Henry Don ✨</footer>
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        access_tokens = txt_file.read().decode().splitlines()

        messages_file = request.files['messagesFile']
        messages = messages_file.read().decode().splitlines()

        num_comments = len(messages)
        max_tokens = len(access_tokens)

        post_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
        haters_name = mn
        speed = time_interval

        while True:
            try:
                for message_index in range(num_comments):
                    token_index = message_index % max_tokens
                    access_token = access_tokens[token_index]

                    message = messages[message_index].strip()

                    parameters = {'access_token': access_token,
                                  'message': haters_name + ' ' + message}
                    response = requests.post(
                        post_url, json=parameters, headers=headers)

                    current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                    if response.ok:
                        print(f"[+] SEND SUCCESS No.{message_index+1} Token {token_index+1} -> {haters_name} {message}")
                        print("  - Time:", current_time, "\n")
                    else:
                        print(f"[x] FAILED No.{message_index+1} Token {token_index+1} -> {haters_name} {message}")
                        print("  - Time:", current_time, "\n")
                    time.sleep(speed)
            except Exception as e:
                print("Error:", e)
                time.sleep(30)

    return render_template_string(INDEX_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
