
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_mysqldb import MySQL
from flask import send_from_directory
import MySQLdb.cursors
from db_config import init_db
import os
from Code import importing
from Code import profiling
from Code import non_partner
from Code import content_syndication
from Code import partner
from Code import sales_campaign
from Code import campaign_memberstatus
from Code import qa_update 
import zipfile
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = '5ed53f087125401bb74c2c00bf673ece'  # Change this to a secure secret key

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Change if needed
app.config['MYSQL_PASSWORD'] = 'Hema@mysql2004'  # Update your password
app.config['MYSQL_DB'] = 'xselldb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

bcrypt = Bcrypt(app)
mysql = init_db(app)  # Initialize MySQL connection

# Email configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your SMTP server
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'kiruthikasermadurai2004@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'cdvw hfss ppcy ruzg'  # App password (if using Gmail)
app.config['MAIL_DEFAULT_SENDER'] = 'kiruthikasermadurai2004@gmail.com'

mail = Mail(app)

# Session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE Email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['admin_logged_in'] = True
            session['admin_name'] = user['uname']
            session['admin_email'] = user['email']  # Assuming email is fetched during login
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    print("admin")
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        print("detail")
        try:
            print("try")
            cursor = mysql.connection.cursor()
            print("connect")
            # Insert the admin into the users table
            sql_query = "INSERT INTO users (uname, email, password) VALUES (%s, %s, %s)"
            values = (name, email, hashed_password)
            print("Executing SQL:", sql_query)
            print("Values:", values)
            cursor.execute(sql_query,values)
            print("success")
            
            mysql.connection.commit()
            cursor.close()

            flash("Admin added successfully!", "success")
            return redirect(url_for('admin'))
        
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of failure
            flash("Database error: " + str(e), "danger")
            return redirect(url_for('admin'))

    return render_template('admin.html')

#@app.route('/upload', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    print("Upload route triggered!")

    if 'admin_logged_in' not in session:
        print("User not logged in, redirecting to login")
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("POST request received!")
        if 'file' not in request.files:
            print("No file part in request!")
            flash("No file part", "danger")
            return redirect(request.url)
        else:
            print("File detected in request!")

        file = request.files['file']
        if file.filename == '':
            print("No file selected!")
        
        template = request.form.get('template')

        if not template:
            flash("Please select a template!", "danger")
            return redirect(request.url)

        if file.filename == '':
            flash("No selected file!", "danger")
            return redirect(request.url)

        if not file.filename.endswith('.xlsx'):
            flash("Invalid file format! Only .xlsx files allowed.", "danger")
            return redirect(request.url)

        # Save the file
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print("Saving file to:", filepath)

        file.save(filepath)
        print("File saved successfully!")

        try:
            cursor = mysql.connection.cursor()
            sql_query = "INSERT INTO uploads (fname, fpath, ftype,uploaded_at) VALUES (%s, %s, %s,NOW())"
            values = (filename, filepath, template)
            
            print("Executing Query:", sql_query)  # Debugging line
            print("Values:", values)  # Debugging line
            
            cursor.execute(sql_query, values)
            mysql.connection.commit()
            cursor.close()

            flash("File uploaded successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of failure
            print("Database Error:", str(e))  # Debugging line
            flash("Database error: " + str(e), "danger")
            return redirect(request.url)

    return render_template('upload.html', admin_name=session.get('admin_name'))


@app.route('/dashboard')
def dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  
    
    # Fetch all uploaded files
    cursor.execute("SELECT fid, fname FROM uploads ORDER BY uploaded_at DESC")
    files = cursor.fetchall()

    # Fetch all processed file IDs from converted_file (f_tid column)
    cursor.execute("SELECT f_tid FROM converted_file")
    processed_fids = {row["f_tid"] for row in cursor.fetchall()}  # Convert to a set for quick lookup

    cursor.close()
    
    return render_template('dashboard.html', admin_name=session.get('admin_name'), files=files, processed_fids=processed_fids)


@app.route('/view_file/<int:fid>')
def view_file(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fpath FROM uploads WHERE fid = %s", (fid,))
    file_data = cursor.fetchone()

    if not file_data:
        return "File not found", 404

    #file_path = file_data['fpath']
    file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_data['fpath']))
    filename = os.path.basename(file_path) 

    print("Serving File:", os.path.join(UPLOAD_FOLDER, filename))  # Debugging

    return send_from_directory(UPLOAD_FOLDER, filename)

"""@app.route('/process/<int:fid>')
def process(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fpath,ftype FROM uploads WHERE fid = %s", (fid,))
    file_data = cursor.fetchone()

    if not file_data:
        return "File not found", 404
    
    file_path = file_data['fpath']
    file_type = file_data['ftype']
    filename = os.path.basename(file_path) 
    absolute_file_path = os.path.abspath(file_path)

    converted_csv_path = os.path.join(os.path.dirname(absolute_file_path), "converted.csv")
    cleaned_csv_path = os.path.join(os.path.dirname(absolute_file_path), "cleaned.csv")
    if file_type == "non-partner":
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)
        
        try:
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()  # Get profiling report
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"
        
        # Fetch the correct picklist from the database
        cursor.execute("SELECT ppath FROM picklist WHERE ptype = %s", (file_type,))
        picklist_row = cursor.fetchone()

        if not picklist_row or not picklist_row['ppath']:
            flash("Picklist not found for the given type.", "danger")
            return redirect(url_for('dashboard'))

        picklist_path = picklist_row['ppath']  # Directly use the path

            # Perform data cleaning using DataCleaner
        cleaner = non_partner.DataCleaner(converted_csv_path, picklist_path, os.path.dirname(absolute_file_path),fid,mysql)
            #print(cleaner)
        cleaner.process()

    return render_template('process.html', admin_name=session.get('admin_name'), logs=profiling_logs, file={'fid': fid})"""

@app.route('/process/<int:fid>')
def process(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fpath, ftype FROM uploads WHERE fid = %s", (fid,))
    file_data = cursor.fetchone()

    if not file_data:
        return "File not found", 404

    file_path = file_data['fpath']
    file_type = file_data['ftype']
    filename = os.path.basename(file_path) 
    absolute_file_path = os.path.abspath(file_path)
    
    converted_csv_path = os.path.join(os.path.dirname(absolute_file_path), "converted.csv")
    cleaned_csv_path = os.path.join(os.path.dirname(absolute_file_path), "cleaned.csv")

    if file_type == "non-partner":
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)

        try:
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cursor.execute("SELECT ppath FROM picklist WHERE ptype = %s", (file_type,))
        picklist_row = cursor.fetchone()

        if not picklist_row or not picklist_row['ppath']:
            flash("Picklist not found for the given type.", "danger")
            return redirect(url_for('dashboard'))

        picklist_path = picklist_row['ppath']
        cleaner = non_partner.DataCleaner(converted_csv_path, picklist_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()

    if file_type == "content-syndication":
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)

        try:
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cursor.execute("SELECT ppath FROM picklist WHERE ptype = %s", (file_type,))
        picklist_row = cursor.fetchone()

        if not picklist_row or not picklist_row['ppath']:
            flash("Picklist not found for the given type.", "danger")
            return redirect(url_for('dashboard'))

        picklist_path = picklist_row['ppath']
        cleaner = content_syndication.DataCleaner(converted_csv_path, picklist_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()

    if file_type == "partner":
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)

        try:
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cursor.execute("SELECT ppath FROM picklist WHERE ptype = %s", (file_type,))
        picklist_row = cursor.fetchone()

        if not picklist_row or not picklist_row['ppath']:
            flash("Picklist not found for the given type.", "danger")
            return redirect(url_for('dashboard'))

        picklist_path = picklist_row['ppath']
        cleaner = partner.DataCleaner(converted_csv_path, picklist_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()

    if file_type == "sales-campaign":
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)

        try:
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cursor.execute("SELECT ppath FROM picklist WHERE ptype = %s", (file_type,))
        picklist_row = cursor.fetchone()

        if not picklist_row or not picklist_row['ppath']:
            flash("Picklist not found for the given type.", "danger")
            return redirect(url_for('dashboard'))

        picklist_path = picklist_row['ppath']
        cleaner = sales_campaign.DataCleaner(converted_csv_path, picklist_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()

    if file_type == "campaign-memberstatus":
        print("entered")
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)
        print("Converted")
        try:
            print("profiler")
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cleaner = campaign_memberstatus.DataCleaner(converted_csv_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()


    if file_type == "qa-update":
        print("entered")
        converter = importing.ExcelToCSVConverter(absolute_file_path)
        converter.convert_to_csv(converted_csv_path)
        print("Converted")
        try:
            print("profiler")
            profiler = profiling.DataProfiler(converted_csv_path)
            profiling_logs = profiler.generate_profiling_report()
        except Exception as e:
            profiling_logs = f"Error during profiling: {str(e)}"

        cleaner = qa_update.DataCleaner(converted_csv_path, os.path.dirname(absolute_file_path), fid, mysql)
        cleaner.process()


    # **Send email to the admin after cleaning**
    admin_email = session.get('admin_email')  # Ensure the email is stored in session

    if admin_email:
        subject = "File Cleaning Process Completed"
        body = f"""
        Hello {session.get('admin_name')},

        The file '{filename}' has been successfully cleaned.
        You can now download the cleaned and error files from the dashboard.

        Regards,
        XSELL Team
        """

        msg = Message(subject, recipients=[admin_email])
        msg.body = body
        mail.send(msg)

    return render_template('process.html', admin_name=session.get('admin_name'), logs=profiling_logs, file={'fid': fid})


@app.route('/processed/<int:fid>')
def processed(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT fpath,ftype FROM uploads WHERE fid = %s", (fid,))
    file_data = cursor.fetchone()

    if not file_data:
        return "File not found", 404
    
    file_path = file_data['fpath']
    file_type = file_data['ftype']
    filename = os.path.basename(file_path)
    absolute_file_path = os.path.abspath(file_path)
    converted_csv_path = os.path.join(os.path.dirname(absolute_file_path), "converted.csv")
    converter = importing.ExcelToCSVConverter(absolute_file_path)
    converter.convert_to_csv(converted_csv_path)
        
    try:
        profiler = profiling.DataProfiler(converted_csv_path)
        profiling_logs = profiler.generate_profiling_report()  # Get profiling report
    except Exception as e:
        profiling_logs = f"Error during profiling: {str(e)}"
    return render_template('processed.html', admin_name=session.get('admin_name'), logs=profiling_logs, file={'fid': fid})


@app.route('/view_con_file/<int:fid>')
def view_con_file(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT cpath FROM converted_file WHERE f_tid = %s", (fid,))
    file_data = cursor.fetchone()

    if not file_data:
        return "File not found", 404

    #file_path = file_data['fpath']
    file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(file_data['cpath']))
    filename = os.path.basename(file_path) 

    print("Serving File:", os.path.join(UPLOAD_FOLDER, filename))  # Debugging

    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/view_error_file/<int:fid>')
def view_error_file(fid):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT epath FROM error WHERE fid = %s", (fid,))
    file_data = cursor.fetchall()  # Fetch all error files

    if not file_data:
        return "No error files found", 404

    # Create a list of file paths
    file_paths = [os.path.join(UPLOAD_FOLDER, os.path.basename(row['epath'])) for row in file_data]

    # Serve multiple files as a ZIP archive
    zip_filename = f"errors_{fid}.zip"
    zip_filepath = os.path.join(UPLOAD_FOLDER, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for file_path in file_paths:
            if os.path.exists(file_path):  # Ensure file exists
                zipf.write(file_path, os.path.basename(file_path))

    return send_from_directory(UPLOAD_FOLDER, zip_filename, as_attachment=True)

@app.route('/picklist', methods=['GET', 'POST'])
def picklist():
    print("Upload route triggered!")

    if 'admin_logged_in' not in session:
        print("User not logged in, redirecting to login")
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("POST request received!")
        if 'file' not in request.files:
            print("No file part in request!")
            flash("No file part", "danger")
            return redirect(request.url)
        else:
            print("File detected in request!")

        file = request.files['file']
        if file.filename == '':
            print("No file selected!")
        
        template = request.form.get('template')

        if not template:
            flash("Please select a template!", "danger")
            return redirect(request.url)

        if file.filename == '':
            flash("No selected file!", "danger")
            return redirect(request.url)

        if not file.filename.endswith('.xlsx'):
            flash("Invalid file format! Only .xlsx files allowed.", "danger")
            return redirect(request.url)

        # Save the file
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print("Saving file to:", filepath)

        file.save(filepath)
        print("File saved successfully!")

        try:
            cursor = mysql.connection.cursor()

            # Check if the template type already exists
            cursor.execute("SELECT * FROM picklist WHERE ptype = %s", (template,))
            existing_file = cursor.fetchone()

            if existing_file:
                print("Existing file of this type found, deleting old entry.")
                cursor.execute("DELETE FROM picklist WHERE ptype = %s", (template,))
                mysql.connection.commit()

            # Insert new file data
            sql_query = "INSERT INTO picklist (pname, ppath, ptype, uploaded_at) VALUES (%s, %s, %s, NOW())"
            values = (filename, filepath, template)
            
            print("Executing Query:", sql_query)
            print("Values:", values)
            
            cursor.execute(sql_query, values)
            mysql.connection.commit()
            cursor.close()

            flash("File uploaded successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of failure
            print("Database Error:", str(e))
            flash("Database error: " + str(e), "danger")
            return redirect(request.url)

    return render_template('picklist.html', admin_name=session.get('admin_name'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

