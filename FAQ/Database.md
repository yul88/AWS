# Database
概述TBD

---
### RDS的一些限制

* 没有root权限，如果要执行一些底层命令，可以参考[MySQL常用DBA命令](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Appendix.MySQL.CommonDBATasks.html)和[PostgreSQL常用DBA命令](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.html)。

* RDS的修改可能会需要重启。是否需要重启，可以参考[这个页面](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Overview.DBInstance.Modifying.html)。

* RDS停止以后，最多停止*7天*。如果7天之内没有启动，则在7天后会自动启动，目的是保持Patch跟上进度。

* RDS的EBS磁盘可以在线自动扩展，也可以手动扩展，但是有需要注意的地方：
    * 只能扩展，不能收缩
    * 自动扩展的大小是max(5GB, 10%, FreeStorageSpace in 7hr)
    * 手动扩展至少要增加现有空间的10%
    * 每次扩展后会有6小时的冷却时间，过了6小时之后才能再次扩展。如果预期有大量数据插入，最好提前手动扩展出足够的空间，

* RDS PG的RDS的*pg_authid*表没有开放给用户，因此数据库的user信息无法导出。通过dump方法重建PG的时候，如果user不存在，user所属的object就无法创建。需要首先列出源上的user一览，然后在目标上重建user，才能通过dump文件恢复。

---
### RDS参数组和选项组

RDS用[参数组](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/USER_WorkingWithParamGroups.html)来调整数据库引擎的参数，用[选项组](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/USER_WorkingWithOptionGroups.html)来控制数据库插件的行为。

默认参数组和默认选项组是不能修改的。如果想修改，必须自定义一个参数组或选项组，然后用自定义的组替换默认组。这个替换过程会造成RDS重启。

因此，建议所有RDS启动的时候都用*自定义参数组*和*自定义选项组*。这个自定义的组可以从默认组复制，需要的时候才修改内容，这样能减少RDS重启。

参数组中*可修改*项为*true*的参数都可以修改。应用类型为*dynamic*的参数修改不需要重启RDS，*static*的参数在重启后才能生效。

---
### Redshift

Redshift有两个选项可以推迟升级:
* 总是选择使用上一个版本：redshift > 修改集群 > 维护 > 维护跟踪 > 早先版本
* 临时终止升级45天：redshift > 修改集群 > 维护 > 推迟维护时段 > Defer maintenance > 已启用

Redshift的终端节点没有分为读写终端节点和只读终端节点。可以通过创建只读用户的方法来限制用户修改数据。
```SQL
-- 创建ro_group用来管理只读用户
CREATE GROUP ro_group;
-- 允许ro_group使用ro_schema并select ro_schema的表
GRANT USAGE ON SCHEMA "ro_schema" TO GROUP ro_group;
GRANT SELECT ON ALL TABLES IN SCHEMA "ro_schema" TO GROUP ro_group;
-- 允许ro_group对未来新创建的表也有select权限
ALTER DEFAULT PRIVILEGES IN SCHEMA "ro_schema" GRANT SELECT ON TABLES TO GROUP ro_group;
-- 禁止ro_group create
REVOKE CREATE ON SCHEMA "ro_schema" FROM GROUP ro_group;

-- 创建ro_user并加入到ro_group
CREATE USER ro_user WITH password PASSWORD;
ALTER GROUP ro_group ADD USER ro_user;
```
