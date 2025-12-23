# Cloud Services Setup Guide for Vercel Deployment

This guide will help you set up PostgreSQL database and Cloudinary media storage to make your bakery POS fully functional on Vercel.

## Step 1: Set Up PostgreSQL Database (Neon - Free)

### 1.1 Create Neon Account
1. Go to https://neon.tech
2. Click "Sign Up" and create a free account
3. Click "Create a project"
4. Choose a name: `bakery-pos-db`
5. Select region closest to you
6. Click "Create Project"

### 1.2 Get Database URL
1. After project creation, you'll see the connection string
2. Copy the **Connection String** (it looks like):
   ```
   postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require
   ```
3. Keep this safe - you'll need it for Vercel

## Step 2: Set Up Cloudinary (Free)

### 2.1 Create Cloudinary Account
1. Go to https://cloudinary.com/users/register/free
2. Sign up for a free account
3. Verify your email

### 2.2 Get Cloudinary Credentials
1. Go to your Cloudinary Dashboard
2. You'll see three important values:
   - **Cloud Name**: (e.g., `dxxxxx`)
   - **API Key**: (e.g., `123456789012345`)
   - **API Secret**: (e.g., `abcdefghijklmnopqrstuvwxyz`)
3. Keep these safe - you'll need them for Vercel

## Step 3: Configure Vercel Environment Variables

### 3.1 Go to Vercel Dashboard
1. Open https://vercel.com/dashboard
2. Select your `bakery-pos` project
3. Click "Settings" tab
4. Click "Environment Variables" in the left sidebar

### 3.2 Add Environment Variables
Add the following environment variables (click "Add" for each):

**Database Configuration:**
- **Name**: `DATABASE_URL`
- **Value**: Your Neon PostgreSQL connection string
- **Environment**: Production, Preview, Development (select all)

**Cloudinary Configuration:**
- **Name**: `CLOUDINARY_CLOUD_NAME`
- **Value**: Your Cloud Name from Cloudinary dashboard
- **Environment**: Production, Preview, Development (select all)

- **Name**: `CLOUDINARY_API_KEY`
- **Value**: Your API Key from Cloudinary dashboard
- **Environment**: Production, Preview, Development (select all)

- **Name**: `CLOUDINARY_API_SECRET`
- **Value**: Your API Secret from Cloudinary dashboard
- **Environment**: Production, Preview, Development (select all)

**Existing Variables (keep these):**
- `SECRET_KEY`: h5JBG4ZL00mO3jbvMhTvZPQUL4MQ6DLeVy3wvUYtwBRec9gD9e
- `DEBUG`: false

### 3.3 Save and Redeploy
1. Click "Save" for each variable
2. Go to "Deployments" tab
3. Click the three dots on the latest deployment
4. Click "Redeploy"

## Step 4: Initialize Database

After the deployment completes, you need to run migrations and create a superuser.

### Option A: Using Vercel CLI (Recommended)
```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# Login to Vercel
vercel login

# Link your project
vercel link

# Run migrations
vercel env pull .env.local
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Option B: Manual Database Setup
Since Vercel is serverless, you'll need to run migrations from your local machine:

1. Install the packages locally:
   ```bash
   pip install -r requirements.txt
   ```

2. Set the DATABASE_URL environment variable locally:
   ```bash
   # Windows PowerShell
   $env:DATABASE_URL = "your-neon-postgresql-url"
   
   # Windows CMD
   set DATABASE_URL=your-neon-postgresql-url
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. (Optional) Load demo data:
   ```bash
   python manage.py seed_demo
   ```

## Step 5: Upload Existing Media Files to Cloudinary

### 5.1 Upload Logo and Background
1. Go to your Cloudinary Dashboard
2. Click "Media Library"
3. Click "Upload" button
4. Upload your files:
   - `media/products/Logo.png`
   - `media/products/Background.jpg`
5. Note the URLs of uploaded files

### 5.2 Update Database Records (if needed)
If you have existing products with images, you may need to update the image paths in your database to point to Cloudinary URLs.

## Step 6: Test Your Deployment

1. Go to your Vercel URL
2. You should now see:
   - ✅ Logo and background images loading
   - ✅ Login working correctly
   - ✅ All features functional

## Troubleshooting

### Database Connection Issues
- Verify DATABASE_URL is correct in Vercel environment variables
- Check that Neon database is active (free tier may pause after inactivity)
- Ensure connection string includes `?sslmode=require`

### Cloudinary Images Not Loading
- Verify all three Cloudinary environment variables are set correctly
- Check that images are uploaded to Cloudinary Media Library
- Ensure CLOUDINARY_CLOUD_NAME matches your dashboard

### 500 Errors After Login
- Run migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`
- Check Vercel function logs for specific errors

## Cost Information

**Neon PostgreSQL:**
- Free tier: 0.5 GB storage, 1 compute unit
- Sufficient for small to medium applications
- Database may pause after 5 minutes of inactivity (resumes automatically)

**Cloudinary:**
- Free tier: 25 GB storage, 25 GB bandwidth/month
- More than enough for a bakery POS application

**Vercel:**
- Free tier: Unlimited deployments
- 100 GB bandwidth/month
- Serverless function executions included

## Summary

After completing these steps:
1. ✅ PostgreSQL database configured (persistent data)
2. ✅ Cloudinary media storage configured (images work)
3. ✅ All environment variables set in Vercel
4. ✅ Database migrations run
5. ✅ Superuser created
6. ✅ Application fully functional on Vercel

Your bakery POS is now production-ready!
