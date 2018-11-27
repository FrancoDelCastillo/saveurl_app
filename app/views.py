from flask import render_template, flash, redirect, session, url_for, request
from app import app, db, lm
from .models import Users, Emails, Posts
from .forms import SigninForm, SignupForm, AddForm, SelectForm
from sqlalchemy import exc, desc
from datetime import datetime
from urllib.parse import urlparse

from flask_login import login_user, logout_user, current_user, login_required #Flask-Login provides user session management 
from werkzeug.security import check_password_hash, generate_password_hash
from flask_user import UserManager
from .decorators import check_confirmed

from flask_mail import Mail, Message #Email confirmation
from itsdangerous import URLSafeSerializer, SignatureExpired

from requests_html import HTMLSession #Web scraping with requests-HTML
import pafy #Retrieve Youtube content and metadata


USER_ENABLE_USERNAME = False
USER_ENABLE_EMAIL = True #Sign in with email


mail = Mail(app) #Set up SMTP
s = URLSafeSerializer('secret-n-complex') #To serialize to a format that is safe to use in URLs


@lm.user_loader #This callback is used to reload the user object from the user id stored in the session
def user_loader(id):
    return Users.query.get(int(id))


@app.route('/signup',methods=['GET','POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        email = form.email.data
        hashed_password = generate_password_hash(form.password.data)

        if Emails.query.filter_by(email=email).first():
            error = 'Email {} is already registered.'.format(email)
            flash(error)
            return redirect(url_for('signup'))
        else:
            new_user = Users(
                password=hashed_password,
                confirmed=False)
            db.session.add(new_user)
            db.session.commit()

            new_email = Emails(
                email=email,
                confirmed=False,
                main_email=True,
                user_id=new_user.id)
            db.session.add(new_email)
            db.session.commit()

            flash("New user created!")
            
            login_user(new_user) #Log them in with login_user function
            
            #Sending email confirmation
            token = s.dumps(email, salt='email-confirm') #To serialize and sign the token
            msg = Message('Confirm Email', sender='flask.example@gmail.com', recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Your confirmation link is: {}'.format(link)
            mail.send(msg)

            return redirect(url_for('unconfirmed')) #Redirect to url with reduced access

    return render_template('signup.html',form=form)


@app.route('/confirm_email/<token>')
@login_required
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm') #To verify the signature and deserialize the token
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('unconfirmed')) #Redirect to url with reduced access

    signin_email = Emails.query.filter_by(email=email).first()
    signin_user = Users.query.filter_by(id=signin_email.user_id).first()
    
    if signin_email.confirmed:
        flash('account already confirmed!','success')
    else:
        signin_email.confirmed = True
        signin_user.confirmed = True
        db.session.add(signin_email)
        db.session.add(signin_user)
        db.session.commit()
        flash('Your account has been activated successfully!','success')

    return redirect(url_for('index'))


@app.route('/signin',methods=['GET','POST'])
def signin():
    form = SigninForm()       

    if form.validate_on_submit():
        email = form.email.data
        pword = form.password.data
        validate_email = Emails.query.filter_by(email=email,main_email=True).first() #Returns <Emails n°>

        if not validate_email:
            error="Invalid email or doesn't exist. Please, Create an account!"
            flash(error)
            return redirect(url_for('signin'))
        else:
            email_user_id = validate_email.user_id #Returns foreign key
            signin_user = Users.query.filter_by(id=email_user_id).first() #Returns <Users n°>
            validate_pword = check_password_hash(signin_user.password, pword)

            if not validate_pword:
                error="Invalid password!"
                flash(error)
                return redirect(url_for('signin'))
        
        login_user(signin_user) #Users table has relation one to many with Emails table

        return redirect(url_for('index'))

    return render_template('signin.html', form=form)


@app.route('/',methods=['GET','POST'])
@login_required
@check_confirmed
def index():
    signin_email = Emails.query.filter_by(user_id=current_user.id,main_email=True).first()

    return render_template ('index.html', email=signin_email.email)


@app.route('/unconfirmed')
@login_required
def unconfirmed():
    signin_email = Emails.query.filter_by(user_id=current_user.id,main_email=True).first()
    signin_confirmed = current_user.confirmed

    if signin_confirmed:
        return redirect(url_for('index'))

    return render_template('unconfirmed.html', email=signin_email.email)


@app.route('/email_accounts',methods=(['GET','POST']))
@login_required
@check_confirmed
def email_accounts():
    form = AddForm() #Add new email associated to main account

    if form.validate_on_submit():
        email = form.email.data
        main_email = Emails.query.filter_by(user_id=current_user.id, email=email).first()

        if main_email:
            error = 'Email {} is already registered. Please, use another email.'.format(email)
            flash(error)    
        else:
            new_email = Emails(
                email=email,
                confirmed=False,
                main_email=False,
                user_id=current_user.id)
            db.session.add(new_email)
            db.session.commit()
            flash("New email added! Please, check your inbox and confirm email.")

            #Sending confirmation email
            token = s.dumps(email, salt='email-confirm')
            msg = Message('Confirm Email', sender='flask.example@gmail.com', recipients=[email])
            link = url_for('confirm_other_email', token=token, _external=True)
            msg.body = 'Your confirmation link is: {}'.format(link)
            mail.send(msg)
            return redirect(url_for('email_accounts'))

    other_emails = Emails.query.filter_by(user_id=current_user.id,main_email=False).all()
    new_main_email = Emails.query.filter_by(user_id=current_user.id,main_email=True).first()
        
    return render_template('email_accounts.html',form=form,other_emails=other_emails,new_main_email=new_main_email)


@app.route('/confirm_other_email/<token>')
@login_required
def confirm_other_email(token):
    try:
        email = s.loads(token, salt='email-confirm') #To verify the signature and deserialize the data
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('unconfirmed')) #Redirect to url with reduced access

    added_email = Emails.query.filter_by(email=email).first()
    
    if added_email.confirmed:
        flash('account already confirmed!','success')
    else:
        added_email.confirmed = True
        added_email.confirmed_on = datetime.now()
        db.session.add(added_email)
        db.session.commit()
        success_msg='Email {} has been confirmed successfully!'.format(added_email.email)
        flash(success_msg)

    return redirect(url_for('email_accounts'))


@app.route('/change_emails',methods=['GET','POST'])
@login_required
@check_confirmed
def change_emails():
    form = SelectForm()
    main_email = Emails.query.filter_by(user_id=current_user.id, main_email=True).first()
    other_emails = Emails.query.filter_by(user_id=current_user.id, main_email=False).all()

    if request.method == 'POST':
        selected_id_email = request.form.get('emails') #Returns id
        find_email = Emails.query.filter_by(id=selected_id_email).first()

        if find_email.confirmed:    
            find_email.main_email = True
            main_email.main_email = False    
            db.session.commit()
            flash('The main email has been changed!','success')
            return redirect(url_for('email_accounts'))
        else:
            flash('Please confirm your email!')
            return redirect(url_for('change_emails'))
    
    return render_template('change_emails.html',other_emails=other_emails,form=form)


@app.route('/save_url',methods=['POST','GET'])
@login_required
def save_url(): #Web scraping and feed
    posts = Posts.query.order_by(desc('created'))    
  
    if request.method == "POST":
        try:
            sess = HTMLSession() #Init Requests-HTML
            saved_url = request.form.get('url')
            parse_url = urlparse(saved_url) #Parsing saved URL into scheme, netloc, path, params, query, fragment
            scheme_url = parse_url.scheme
            base_url = parse_url.netloc

            r = sess.get(saved_url) #Request HTML from saved URL
            scrape_title = r.html.find('title',first=True).text #Scraping title
            scrape_img = r.html.xpath('//link[@rel="icon" or @rel="shortcut icon"]/@href') #Scraping image option n°1, it could returns a list
            scrape_img2 = r.html.xpath('//img/@src') #Scraping image option n°2, it could returns a list
            
            if scrape_img:
                scrape_img = scrape_img[0] #Option n°1 first element
            else:
                scrape_img = scrape_img2[0] #Option n°2 first element

            parse_url_img = urlparse(scrape_img) #Parsing image's URL

            if not parse_url_img.netloc:
                scrape_img = scheme_url + '://' + base_url + scrape_img

            if base_url == 'www.youtube.com':
                video_url = parse_url.query #Extract the video ID
                scrape_img = 'https://i.ytimg.com/vi/'+video_url[2:]+'/hqdefault.jpg' #Searching thumbnail
                vid = pafy.new(saved_url) #Using pafy to retrieve YouTube's video data
                title_vid = vid.title
                scrape_title = title_vid

            new_post = Posts(
                title=scrape_title,
                url_base=base_url,
                url_img=scrape_img,
                url_dir=saved_url,
                created=datetime.now(),
                user_post=current_user.id)
            db.session.add(new_post)
            db.session.commit()
            sess.close()
            
        except Exception as e:
            print(str(e))
            error = "Unable to get URL. Please make sure it's valid and try again."
            flash(error)
            
    return render_template("save_url.html",posts=posts)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('signin'))