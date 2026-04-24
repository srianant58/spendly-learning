git pull origin master  
git checkout -b feature/database-setup 

git status
git add .
git commit -m "comment"
git checkout -b feature/custom-slash-command
git commit -m "comment1"
git push origin feature/registration
git checkout master
git pull origin master
git branch -D feature/registration
git branch