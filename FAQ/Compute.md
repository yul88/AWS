# Compute
概述TBD

### EC2私钥丢失

AWS不会保存私钥，需要重新创建私钥
1. 关机(*副作用*：非EIP的公网IP会变化，实例存储InstanceStore上的数据会丢失)
2. 把EBS从EC2(A)分离Detach，然后挂载在另一台能登陆的EC2(B)上面
3. mount ebs 到路径，如/mount
4. 修改/mount/home/ec2-user/.ssh/authorized_keys，改成新密钥对中的*公钥*
5. umount /mount
6. 把EBS从EC2(B)分离，重新挂载到EC2(A)
7. EC2(A)开机，用新的密钥对中的*私钥*登陆

