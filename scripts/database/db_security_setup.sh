#!/bin/bash
# MongoDB security setup
docker exec mltb-mongodb mongosh << MONGO_SCRIPT
use admin
db.createUser({
  user: "mltb_admin",
  pwd: "generate_secure_password",
  roles: [
    { role: "root", db: "admin" },
    { role: "dbOwner", db: "mltb" }
  ]
})
db.getSiblingDB('mltb').createUser({
  user: "mltb_user",
  pwd: "generate_user_password",
  roles: [
    { role: "readWrite", db: "mltb" },
    { role: "dbAdmin", db: "mltb" }
  ]
})
MONGO_SCRIPT
