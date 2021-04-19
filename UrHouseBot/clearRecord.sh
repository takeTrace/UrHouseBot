export PROJ=~/.dotfiles/mackup/Projects/MyProject/UrHouseBot/UrHouseBot

rm -f $PROJ/logs/*
echo "{}" > $PROJ/titles.json
echo '{"stop": false}' > configs.json
echo "{}" > groups.json
