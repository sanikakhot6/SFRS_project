import tkinter as tk
from tkinter import Tk,Button,Label,messagebox,scrolledtext
from math import radians,sin,cos
from datetime import datetime
from PIL import Image,ImageTk,ImageDraw
import os
import numpy as np
import cv2
import mysql.connector
import re
import time
import pyttsx3
import openpyxl
import json

FEEDBACK_FILE="feedback.json"

# Initialize text-to-speech engine
#Initialize last spoke time at the beginning
last_spoke_time=0 

def speak_with_cooldown(text):
    global last_spoke_time
    if time.time()-last_spoke_time>5: #5-second cooldown
        speak(text)
        last_spoke_time=time.time()
# Initialize the text-to-speech engine
engine = pyttsx3.init()  # Add this line

# Define the speak function
def speak(text):  # Add this function definition here
   engine.say(text)
   engine.runAndWait()

window=Tk()   # Creates the main application window
window.title("SFRS")    # Sets the window title
speak_with_cooldown("Hello....,Welcome to SMART FACE RECOGNITION SYSTEM")
window.geometry("1000x680")  # Sets the window dimensions to 1000 pixels wide by 650 pixels high

bg_photo=None
preview_label=None
#clock_label = Label(window)

def first_page():
    global bg_photo
    for widget in window.winfo_children():
        widget.destroy()
    #Load the backgroun image
    bg_image=Image.open("C:/Users/Administrator/Desktop/.vscode/header.jpg")
    bg_image=bg_image.resize((1000,680),Image.LANCZOS)
    bg_photo=ImageTk.PhotoImage(bg_image)
    #To create canvas and set the background image
    canvas=tk.Canvas(window,width=1000,height=680)
    canvas.pack(fill="both",expand=True)
    canvas.create_image(0,0,image=bg_photo,anchor="nw")
    
    #Start button here
    start_button=Button(window,text="Start project", font=("Algerian",20),bg="green",command=second_page)
    start_button.place(x=300,y=500)
  
#Function for exit 
def exit_app():
    response=messagebox.askyesno('Feedback',"Do you want to give feedback before exiting?")
    
    #if yes clicked 
    if response:
        give_feedback()
    else: #speak before quitting
        speak_with_cooldown("Thanks for visiting")  # Speak before quitting
        window.quit()  # Close the window 

def update_stars(rating_var, star_buttons):
    """Update the appearance of star buttons based on the rating."""
    for i, star_button in enumerate(star_buttons):
        if i < rating_var.get():
            star_button.config(fg="darkorange")  # Set color of filled stars
        else:
            star_button.config(fg="darkgray")  # Set color of empty stars

def give_feedback():
    #Function to create a window and collect feedback
    feedback_window = tk.Toplevel(window)
    feedback_window.title("Feedback")
    feedback_window.geometry("400x300")

    # Title label
    title_label = tk.Label(feedback_window, text="Please rate the application", font=("Arial", 16))
    title_label.pack(pady=10)

    # Rating variable
    rating_var = tk.IntVar()
    rating_var.set(0)  # Default rating

    # Create star buttons
    star_buttons = []
    star_frame = tk.Frame(feedback_window)  # Create a frame to hold star buttons
    star_frame.pack(pady=10)
    
    for i in range(5):
        star_button = tk.Button(star_frame, text="★", font=("Arial", 20),
                                command=lambda i=i: (rating_var.set(i+1),update_stars(rating_var,star_buttons)))  # Update rating on click
        star_button.pack(side="left", padx=5)
        star_buttons.append(star_button)
        
    # Additional comments label and text box
    comments_label = tk.Label(feedback_window, text="Additional comments (optional):")
    comments_label.pack(pady=5)

    comments_text = tk.Text(feedback_window, height=4, width=35)  # Multi-line text box
    comments_text.pack(pady=5)
 

    # Function to handle feedback submission
    def submit_feedback():
        rating = rating_var.get()
        comment = comments_text.get("1.0", tk.END).strip()
        if not comment:  # If the comment is empty, set a default message
            comment = "No additional comments provided"
        if rating > 0:
            # Save feedback before closing
            save_feedback(rating, comment)
            messagebox.showinfo("Feedback", "Thanks for your feedback!")
            speak_with_cooldown("Thanks for visiting")
            feedback_window.destroy()
            window.quit()  # Exit the application
        else:
            messagebox.showwarning("Feedback", "Please provide a rating.")

    # Submit feedback button
    submit_button = tk.Button(feedback_window, text="Submit Feedback", command=submit_feedback)
    submit_button.pack(pady=10)



# Function to save feedback to a file
def save_feedback(rating, comment):
     # Ensure the comment is not empty
    #if not comment:
     #   comment = "No additional comments provided."

    feedback = {
        "rating": rating,
        "comment": comment
    }

    # Try to load existing feedbacks from the feedback file
    try:
        with open(FEEDBACK_FILE, 'r') as f:
            all_feedbacks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_feedbacks = []

    # Append the new feedback
    all_feedbacks.append(feedback)

    # Save all feedbacks back to the file
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(all_feedbacks, f, indent=4)

def view_feedback():
        """View the saved feedback in a new window with word wrap and a scrollable area."""
        try:
            with open(FEEDBACK_FILE, 'r') as file:
                feedback_list = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            feedback_list = []

        feedback_window = tk.Toplevel(window)
        feedback_window.title("Previous Feedback")
        feedback_window.geometry("500x500")

        # Create a scrollable text area
        scrollable_text = scrolledtext.ScrolledText(feedback_window, wrap=tk.WORD, width=60, height=20, font=("Arial", 12))
        scrollable_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Display each feedback entry with word wrap and delete buttons
        for i, feedback in enumerate(feedback_list):
            rating = "⭐" * feedback["rating"] + "☆" * (5 - feedback["rating"])
            comment = feedback.get("comment", "No comment provided") 
            feedback_text = f"{i + 1}. Rating: {rating}\nComment: {comment}"

            # Insert feedback text
            scrollable_text.insert(tk.END, feedback_text + "\n")

            # Create a delete button for each feedback entry
            delete_button = tk.Button(feedback_window, text="Delete", font=("Arial", 10), 
                                      command=lambda i=i: delete_feedback_and_refresh(i, feedback_window))
            scrollable_text.window_create(tk.END, window=delete_button)
            
            scrollable_text.insert(tk.END, "\n\n")  # Add spacing after each entry

        scrollable_text.config(state=tk.DISABLED)  # Make the feedback read-only

        close_button = tk.Button(feedback_window, text="Close", font=("Arial", 12), command=feedback_window.destroy)
        close_button.pack(pady=10)

def delete_feedback_and_refresh(index, feedback_window):
        """Delete the feedback entry, refresh the feedback window to reflect deletion."""
        delete_feedback(index)
        feedback_window.destroy()
        view_feedback()  # Re-open the feedback window to show updated list

def delete_feedback(index):
        """Delete the feedback entry and update the file."""
        try:
            with open(FEEDBACK_FILE, 'r') as file:
                feedback_list = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            messagebox.showerror("Error", "No feedback to delete.")
            return

        # Remove the feedback at the given index
        feedback_list.pop(index)

        # Save the updated feedback list back to the file
        with open(FEEDBACK_FILE, 'w') as file:
            json.dump(feedback_list, file, indent=4)

        messagebox.showinfo("Feedback Deleted", "Feedback has been deleted successfully.")

#Second page 
def second_page():
    global bg_photo
    for widget in window.winfo_children():
        widget.destroy()

    #Load the backgroun image
    bg_image=Image.open("C:/Users/Administrator/Desktop/.vscode/Myproject/bg1.jpeg")
    bg_image=bg_image.resize((1000,680),Image.LANCZOS)
    bg_photo=ImageTk.PhotoImage(bg_image)

    #To create canvas and set the background image
    canvas=tk.Canvas(window,width=1000,height=680)
    canvas.pack(fill="both",expand=True)
    canvas.create_image(0,0,image=bg_photo,anchor="nw")

    # Create the blank section (rectangle) inside the background
    canvas.create_rectangle(110, 150, 900, 550, outline="white",fill="light grey", width=2)

    #for clock 
    def clock_image(hr,min_,sec_):
        clock=Image.new("RGB",(400,395),(0,0,0))
        draw=ImageDraw.Draw(clock)

        for i in range(12):
            angle=radians(i*30)
            x1=200+90*sin(angle)
            y1=200-90*cos(angle)
            x2=200+100*sin(angle)
            y2=200-100*cos(angle)
            draw.line((x1,y1,x2,y2),fill="white",width=2)
        
        #Clock hands draw
        origin = 200, 200
        draw.line((origin, 200 + 50 * sin(radians(hr)), 200 - 50 * cos(radians(hr))), fill="white", width=6)
        draw.line((origin, 200 + 70 * sin(radians(min_)), 200 - 70 * cos(radians(min_))), fill="lightgrey", width=4)
        draw.line((origin, 200 + 90 * sin(radians(sec_)), 200 - 90 * cos(radians(sec_))), fill="red", width=2)

        #Center circle drawing
        draw.ellipse((195, 195, 205, 205), fill="cyan")
        clock.save("clock_new2.png")

    def update_clock():
        now=datetime.now()
        hr=(now.hour%12)*30+ (now.minute * 0.5)
        min_=now.minute*6
        sec_=now.second*6

        clock_image(hr, min_, sec_)
        clock_img = ImageTk.PhotoImage(file="clock_new2.png")
        clock_label.config(image=clock_img)
        clock_label.image = clock_img

        clock_label.after(1000, update_clock)
    
    #Clock display
    global clock_label
    clock_label=Label(window)
    clock_label.place(x=110, y=150)

    # Detect and Generate dataset buttons
    b1 = Button(window, text="Detect face", font=("Algerian", 20), bg='green', fg='white',command=detect_face)
    b2 = Button(window, text="Generate dataset", font=("Algerian", 20), bg='pink', fg='black',command=third_page)
    b3 = Button(window, text="Search data", font=("Algerian", 20), bg='purple', fg='white',command=save_persons_data_to_excel)
    b4 = Button(window, text="Reviews", font=("Algerian", 20), bg='lightblue', fg='black',command=view_feedback)

    # Show buttons inside the blank section
    b1.place(x=550, y=180)
    b2.place(x=550, y=280)
    b3.place(x=550, y=380)
    b4.place(x=550 ,y=480)

    back_button=Button(window,text="Back", font=("Algerian",20),bg="red",command=first_page)
    back_button.place(x=30,y=570)
    exit_button=Button(window,text="Exit", font=("Algerian",20),bg="red",command=exit_app)
    exit_button.place(x=870,y=570)  

    #start the clock update loop 
    update_clock()

def validate_inputs():
    # Name validation: allows alphabets and spaces
    if not t1.get().strip().replace(" ", "").isalpha():
        messagebox.showerror("Validation Error", "Name should contain only letters and spaces.")
        return False

    # Age validation: check if it's a valid number and within a reasonable range
    try:
        age = int(t2.get().strip())
        if age < 12 or age > 80:
            messagebox.showerror("Validation Error", "Age should be between 12 and 80.")
            return False
    except ValueError:
        messagebox.showerror("Validation Error", "Age should be a valid number.")
        return False

    # Gender validation: check if gender is one of the allowed options, case-insensitively
    gender = t3.get().strip().lower()  # Convert to lowercase for case-insensitive comparison
    if gender not in ["male", "female", "other"]:
        messagebox.showerror("Validation Error", "Gender should be 'Male', 'Female', or 'Other'.")
        return False

    # Address validation: ensure it's not empty
    if not t4.get().strip():
        messagebox.showerror("Validation Error", "Address cannot be empty.")
        return False

    # Contact number validation: must be a 10-digit number
    contact_no = t5.get().strip()
    if not re.match(r"^\d{10}$", contact_no):
        messagebox.showerror("Validation Error", "Contact number should be a 10-digit number.")
        return False

    # All validations passed
    return True

    
#Define the function for training the classifier
def train_data():
    data_dir="C:/Users/Administrator/Desktop/.vscode/Myproject/data"
    path=[os.path.join(data_dir,f) for f in os.listdir(data_dir) ]
    faces=[]
    ids=[]

    for image in path:
        img=Image.open(image).convert('L')
        imageNp=np.array(img,'uint8')
        id=int(os.path.split(image)[1].split(".")[1])

        faces.append(imageNp)
        ids.append(id)
    ids=np.array(ids)

    #Train the classifier and save
    clf=cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces,ids)
    clf.write("Classifier.xml")

    #speak("data has saved successfully")
    messagebox.showinfo("Form","data saved successfully")

#defining the function for saving the data 
def save_button():
    global preview_label  
    #Check if any field is empty after validation
    if t1.get()=="" or t2.get()=="" or t3.get() == "" or t4.get() == "" or t5.get() == "":
        #speak("incomplete information")
        messagebox.showinfo("form",'Please provide complete details')
        return
    
    #Validate inputs
    if not validate_inputs():
        return
    
    try:
        mydb=mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="tiger",
            database="Authorized_user"
        )
        mycursor=mydb.cursor()

        #Check if the person is already in the database
        name=t1.get().strip()
        contact_no=t5.get().strip()
        mycursor.execute("SELECT * FROM my_table WHERE Name=%s OR Contact_No=%s",(name,contact_no))
        existing_user=mycursor.fetchone()

        if existing_user:
            speak_with_cooldown("dataset already exit ")
            messagebox.showinfo("form", "Person dataset already exists.")
            return

        #Assign a new ID for the new user
        mycursor.execute("SELECT MAX(id) FROM my_table")
        max_id=mycursor.fetchone()[0]
        new_id=max_id + 1 if max_id else 1

        #insert new data
        sql="INSERT INTO my_table (id,Name,Age,Gender,Address,Contact_No) VALUES (%s,%s,%s,%s,%s,%s)"
        val= (new_id,t1.get(),t2.get(),t3.get(),t4.get(),t5.get())
        mycursor.execute(sql,val)
        mydb.commit()

        #Load face Classifier
        face_classifier=cv2.CascadeClassifier("C:/Users/Administrator/Desktop/.vscode/Myproject/haarcascade_frontalface_default.xml")

        def face_cropped(img):
            gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray,1.3,5)
            for (x,y,w,h) in faces:
                return img[y:y +h,x:x+w]
            return None
        
        #Capture faces and save them
        cap=cv2.VideoCapture(1)
        img_id=0

        while True:
            ret,frame=cap.read()
            if not ret:
                messagebox.showerror("image Error","Failed to capture image")
                break

            cropped_face=face_cropped(frame)
            if cropped_face is not None:
                img_id +=1
                face=cv2.resize(cropped_face,(200,200))
                face=cv2.cvtColor(face,cv2.COLOR_BGR2GRAY)
                file_name_path=f"C:/Users/Administrator/Desktop/.vscode/Myproject/data/user.{new_id}.{img_id}.jpg"
                cv2.imwrite(file_name_path,face)

                # Update preview with each new image
                face_img = Image.open(file_name_path)
                face_photo = ImageTk.PhotoImage(face_img)
                preview_label.config(image=face_photo)
                preview_label.image = face_photo  # Prevent garbage collection


                #Display feedback
                cv2.putText(face,str(img_id),(50,50),cv2.FONT_HERSHEY_COMPLEX,1,(0,255,0),2)
                cv2.imshow("Cropped Face",face)

                if cv2.waitKey(1)==13 or img_id==20:
                    break
        
        #Release resources
        cap.release()
        cv2.destroyAllWindows()

        #Call the train_data function after the dataset is created
        train_data()


    except mysql.connector.Error as err:
        messagebox.showerror("DataBase Error",f"An error occureed {err}")
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()   

def third_page():
    global preview_label 
    for widget in window.winfo_children():
        widget.destroy()

     # Create an outer frame with a border around the entire window
    outer_frame = tk.Frame(window, bd=10, relief="solid", padx=20, pady=20)
    outer_frame.place(x=10, y=10, width=980, height=650)  

    # Define labels and entry fields (initially hidden)
    global t1, t2, t3, t4, t5  # Declare these as global so we can access them later

    # Define labels and entry fields (initially hidden)
    l1 = tk.Label(window, text="Name : ", font=("Algerian", 15))
    t1 = tk.Entry(window, width=50, bd=5)
    l2 = tk.Label(window, text="Age : ", font=("Algerian", 15))
    t2 = tk.Entry(window, width=50, bd=5)
    l3 = tk.Label(window, text="Gender : ", font=("Algerian", 15))
    t3 = tk.Entry(window, width=50, bd=5)
    l4 = tk.Label(window, text="Address : ", font=("Algerian", 15))
    t4 = tk.Entry(window, width=50, bd=5)
    l5 = tk.Label(window, text="Contact No. : ", font=("Algerian", 15))
    t5 = tk.Entry(window, width=50, bd=5)
    
    l1.place(x=50, y=50)
    t1.place(x=200, y=50)
    l2.place(x=50, y=100)
    t2.place(x=200, y=100) 
    l3.place(x=50, y=150)
    t3.place(x=200, y=150)
    l4.place(x=50,y=200)
    t4.place(x=200,y=200)
    l5.place(x=50,y=250)
    t5.place(x=200,y=250)   

    tk.Button(window, text="Save", font=("Algerian", 15), bg='purple', fg='white',command=save_button).place(x=150, y=300)

    # Inside your third_page function, add a label to the right side
    preview_label = Label(window)  # Label to display captured image
    preview_label.place(x=600, y=50)  # Adjust coordinates to your layout

    back_button=Button(window,text="Back", font=("Algerian",20),bg="red",command=second_page)
    back_button.place(x=30,y=570)

    exit_button=Button(window,text="Exit", font=("Algerian",20),bg="red",command=exit_app)
    exit_button.place(x=870,y=570) 

     # Bind the Enter key to move focus to the next textbox
    t1.bind("<Return>", lambda event: t2.focus_set())
    t2.bind("<Return>", lambda event: t3.focus_set())
    t3.bind("<Return>", lambda event: t4.focus_set())
    t4.bind("<Return>", lambda event: t5.focus_set())

def refresh_page(event=None):
        third_page()  # Calls the third_page function to reload it
# Bind F5 to refresh_page
window.bind('<F5>', refresh_page)  

#Database connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="tiger", 
            database="Authorized_user"
        )
    except mysql.connector.Error as err:
        messagebox.showerror('Database Error', f'Error: {err}')
    return

#for csv file (search list button)
def save_persons_data_to_excel():
    speak(f'Please wait, file is opening')
    mydb=get_db_connection()    
    if not mydb:
        return #stop
    mycursor = mydb.cursor()
    mycursor.execute("SELECT id, Name, Age, Gender, Address, Contact_No FROM my_table")
    users = mycursor.fetchall()

    # Define the Excel file path
    excel_file_path = "persons_data_with_images.xlsx"

    try:
        # Create a new workbook and a sheet
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Persons Data"
        
        # Write the header row
        sheet.append(['ID', 'Name', 'Age', 'Gender', 'Address', 'Contact No', 'Image'])
        
        # Write user data and insert images
        for i, user in enumerate(users, start=2):  # Start from row 2
            sheet[f'A{i}'] = user[0]  # ID
            sheet[f'B{i}'] = user[1]  # Name
            sheet[f'C{i}'] = user[2]  # Age
            sheet[f'D{i}'] = user[3]  # Gender
            sheet[f'E{i}'] = user[4]  # Address
            sheet[f'F{i}'] = user[5]  # Contact No

            # Construct the image file path for the user
            image_path = f"C:/Users/Administrator/Desktop/.vscode/Myproject/data/user.{user[0]}.1.jpg"
            
            # Check if the image exists before adding it
            if os.path.exists(image_path):
                # Create a hyperlink in the 'Image' column
                sheet[f'G{i}'] = f"image"
                sheet[f'G{i}'].hyperlink = image_path
            else:
                print(f"Image not found for ID {user[0]}: {image_path}")  # Debugging message for missing images
        
        # Save the workbook to the Excel file
        wb.save(excel_file_path)
        
        # Open the Excel file automatically
        os.startfile(excel_file_path)
        
    except Exception as e:
        messagebox.showerror('File Error', f'Error saving to Excel: {e}')
    
    mydb.close()

#function to display user info
def display_user_details(user_id):
    mydb=get_db_connection()
    if not mydb:
        return
    mycursor=mydb.cursor()
    mycursor.execute("SELECT * FROM my_table WHERE id=%s",(user_id,))
    user_details=mycursor.fetchone()

    #Create a new window to display user details
    details_window=tk.Toplevel(window)
    details_window.title("User Details")
    details_window.geometry("400x400")
    details_window.configure(bg="white")

    image_path = f"C:/Users/Administrator/Desktop/.vscode/Myproject/data/user.{user_id}.1.jpg" 

    #Load and display the image
    if os.path.exists(image_path):
        user_image = Image.open(image_path)
        user_image = user_image.resize((150, 150), Image.LANCZOS)
        user_photo = ImageTk.PhotoImage(user_image)
        
        image_label = tk.Label(details_window, image=user_photo, bg="white")
        image_label.image = user_photo 
        image_label.pack(pady=10)
    else:
        tk.Label(details_window, text="No image found for this user.", font=("Algerian", 12), bg="white", fg="red").pack(pady=10)

    #display user details
    if user_details:
        details_text=f"Name: {user_details[1]}\n Age: {user_details[2]}\n Gender: {user_details[3]}\n Address: {user_details[4]}\n Contact No.: {user_details[5]}"
        tk.Label(details_window,text=details_text,font=("Algerian", 15), bg="white").pack(pady=20)
    else:
        messagebox.showinfo("Result","No details found for this ID.")

# Global variable to store face coordinates and IDs
detected_faces = []

#Function for detect faces
def detect_face():
    speak("Please wait,The camera is opening")

    def draw_boundary(img,classifier,scaleFactor,minNeighbours,color,text,clf):
        global detected_faces
        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.equalizeHist(gray_image) #for every light

        # Apply CLAHE to improve image contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_image = clahe.apply(gray_image)

        features=classifier.detectMultiScale(gray_image,scaleFactor,minNeighbours)
         # Create the window to ensure it exists for the callback
        cv2.namedWindow("Face Detection")
        #coords=[]
        detected_faces = []

        for (x,y,w,h) in features:
            cv2.rectangle(img,(x,y),(x+w,y+h),color,2)
            id,pred=clf.predict(gray_image[y:y + h,x:x+w])
            confidence=int(100*(1-pred/300))

            mydb=get_db_connection()            
            if mydb:
                try:
                    mycursor = mydb.cursor()
                    mycursor.execute("SELECT name FROM my_table WHERE id = %s", (id,))
                    name_result = mycursor.fetchone()

                    # If face is found in the database and confidence is high, display the name
                    if name_result and confidence > 75:
                        box_color = (255, 255, 255)
                        s = ''.join(name_result)  # Person's name
                        cv2.putText(img, s, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8,(255,255,255), 2, cv2.LINE_AA)
                        detected_faces.append({"id": id, "x": x, "y": y, "w": w, "h": h})
                    else:
                        box_color = (0, 0, 255)
                        # If not recognized or confidence is low, display "UNKNOWN" in red
                        cv2.putText(img, "UNKNOWN", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 1, cv2.LINE_AA)
                        speak_with_cooldown("Unknown person detected.")
                    # Draw the rectangle with the appropriate box color
                    cv2.rectangle(img, (x, y), (x + w, y + h), box_color, 2)
                finally:
                    mydb.close()  # Ensure the database connection is closed
        return img
    
 # Mouse click event handler
    def on_click(event, x_click, y_click, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for face in detected_faces:
                x, y, w, h = face["x"], face["y"], face["w"], face["h"]
                # Check if click is within the bounding box of a detected face
                if x < x_click < x + w and y < y_click < y + h:
                    display_user_details(face["id"])
                    break

    # Recognize faces in the video feed
    def recognize(img, clf, faceCascade):
        img = draw_boundary(img, faceCascade, 1.1, 10, (255, 255, 255), "Face", clf)
        return img

    # Load face classifier and recognizer model
    faceCascade = cv2.CascadeClassifier("C:/Users/Administrator/Desktop/.vscode/Myproject/haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier.xml")

    # Start video capture
    video_capture = cv2.VideoCapture(1)
    cv2.namedWindow("Face Detection")
    cv2.setMouseCallback("Face Detection", on_click)  # Set mouse callback

    try:
        while True:
            ret, img = video_capture.read()
            if not ret:
                break
            img = recognize(img, clf, faceCascade)
            cv2.imshow("Face Detection", img)

            if cv2.waitKey(1) == 13:  # Press Enter to exit
                break
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        
first_page()
window.mainloop()    # Starts the Tkinter event loop
