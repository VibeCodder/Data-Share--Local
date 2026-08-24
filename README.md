# File Server
A simple script that enables to share files between devices in the same network.<br>
Program also gives an option to send only text and there is a preview of this text from sent txt file on the file list.
<br><br>
`file_server.py` is the actual python script, <br>
`Text-To-Web_Local.py` is an old version of the program.
<br>
Oto opis w stylu README, gotowy do wklejenia na GitHuba:

---

## Password Setup

The server requires HTTP Basic Auth. The password is resolved in the following order (first match wins):

1. **Environment variable**
   ```bash
   FILE_SERVER_PASSWORD=my-secret-password python3 file_server.py
   ```

2. **Command-line argument**
   ```bash
   python3 file_server.py 8000 my-secret-password
   ```

3. **Password file**
   Create a file named `.file_server_password` in the same directory as the script, containing nothing but the password:
   ```bash
   echo "my-secret-password" > .file_server_password
   chmod 600 .file_server_password
   ```

4. **Auto-generated (default)**
   If none of the above is set, the server generates a random password at startup and prints it to the console.

> **Note:** The username is fixed as `admin`. If you use the password file, make sure to add it to `.gitignore` and restrict its file permissions, since it's stored in plain text.
<br><br>
You can also run the app without https using this command:
```
$env:FILE_SERVER_NO_HTTPS="1"; python file_server.py
```
You must also install:

```
pip install tkinterdnd2
```

<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/cea2ce51-3ed3-432c-a16a-fe497ec792c3" />
<br><br><br>
<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/6f15a1d1-bbcf-48b6-9c92-36d88d15c862" />
