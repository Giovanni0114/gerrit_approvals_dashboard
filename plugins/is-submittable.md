# PLUGIN TO CHECH IF  CHANGE IS SUBMITTABLE


### When triggered:
after approval changes
AND
There's no negative verification

###
Try to call command via gerrit ssh query


```sh
ssh -p 29418 USER@GERRIT-SERVER gerrit query /number/ is:submittable
```

if the change is returned, add comment READY TO SUBMIT

