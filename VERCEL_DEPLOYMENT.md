# Vercel Deployment Notes

## Current Status
✅ Application is deployed and accessible on Vercel
✅ Django is running successfully
⚠️ Limited functionality due to serverless constraints

## Known Limitations

### 1. Database
- Vercel's serverless environment doesn't support persistent SQLite databases
- Currently using in-memory database (data resets on each deployment)
- **Solution**: Use a cloud database like PostgreSQL (Supabase, Neon, etc.)

### 2. Media Files
- User-uploaded images cannot be stored on Vercel's filesystem
- Static media files (Logo.png, Background.jpg) are missing
- **Solution**: Use cloud storage like AWS S3, Cloudinary, or Vercel Blob

### 3. Authentication
- Login will fail because the database resets between requests
- Sessions cannot persist without a proper database
- **Solution**: Implement cloud database for user authentication

## Recommended Next Steps

1. **Set up PostgreSQL Database**
   - Use Supabase (free tier available)
   - Or Neon (serverless PostgreSQL)
   - Update DATABASE_URL environment variable

2. **Set up Media Storage**
   - Use Cloudinary for image hosting
   - Or AWS S3 for file storage
   - Update Django settings for cloud storage

3. **Environment Variables to Add**
   - `DATABASE_URL` - PostgreSQL connection string
   - `CLOUDINARY_URL` - For media file storage (if using Cloudinary)

## Current Environment Variables
- `SECRET_KEY`: h5JBG4ZL00mO3jbvMhTvZPQUL4MQ6DLeVy3wvUYtwBRec9gD9e
- `DEBUG`: false

## For Local Development
The application works fully when run locally with:
```bash
python manage.py runserver
```

All features including database, media uploads, and authentication work correctly in local development.
