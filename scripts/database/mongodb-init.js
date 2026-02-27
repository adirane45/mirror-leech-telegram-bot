// MongoDB Initialization Script
// Creates application user and sets up authentication

// Switch to admin database
db = db.getSiblingDB('admin');

// Create application user if it doesn't exist
admin_user = db.getUser('mltb_bot');
if (admin_user == null) {
  db.createUser({
    user: 'mltb_bot',
    pwd: process.env.MONGO_PASSWORD || 'mltb_password',
    roles: [
      { role: 'dbOwner', db: 'mltb' },
      { role: 'read', db: 'admin' }
    ]
  });
  print("✅ Created application user: mltb_bot");
} else {
  print("⚠️  User mltb_bot already exists");
}

// Switch to application database
db = db.getSiblingDB('mltb');

// Create collections if they don't exist
db.createCollection('downloads', { capped: false });
db.createCollection('uploads', { capped: false });
db.createCollection('tasks', { capped: false });
db.createCollection('users', { capped: false });
db.createCollection('settings', { capped: false });

print("✅ Created application collections");

// Create indexes for performance
db.downloads.createIndex({ 'timestamp': -1 });
db.downloads.createIndex({ 'user_id': 1 });
db.uploads.createIndex({ 'timestamp': -1 });
db.uploads.createIndex({ 'user_id': 1 });
db.tasks.createIndex({ 'status': 1 });
db.tasks.createIndex({ 'user_id': 1 });
db.users.createIndex({ 'user_id': 1 }, { unique: true });

print("✅ Created database indexes");
print("✅ MongoDB initialization complete");
