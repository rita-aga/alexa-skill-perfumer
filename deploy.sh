
#!/usr/bin/env bash

echo "================== Installing requirements to skill_env folder..."
pip install -r requirements.txt -t skill_env

echo "================== Copying code to skill_env folder..."
cp index.py ./skill_env/
cd skill_env/

# zip function code
echo "================== Zipping deploy folder..."
zip -r ../skill.zip *


# deploy to lambda
echo "================== Deploying to lambda..."
cd ..
# aws lambda create-function --function-name alexa_skill_perfumer --runtime python3.7 --role arn:aws:iam::046742733488:role/AlexaRole --handler index --zip-file fileb://./skill.zip
aws lambda update-function-code --function-name alexa_skill_perfumer --zip-file fileb://./skill.zip


# clean up deploy files
echo "================== Cleaning up deploy folder and zip file..."
rm -r -f skill.zip

echo "################ DONE! ################"