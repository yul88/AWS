# Database
概述TBD

---
### RDS的一些限制

* 没有root权限，如果要执行一些底层命令，可以参考[MySQL常用DBA命令](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Appendix.MySQL.CommonDBATasks.html)和[PostgreSQL常用DBA命令](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.html)。

* RDS的修改可能会需要重启。是否需要重启，可以参考[这个页面](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Overview.DBInstance.Modifying.html)。

* RDS停止以后，最多停止**7天**。如果7天之内没有启动，则在7天后会自动启动，目的是保持Patch跟上进度。

* RDS的EBS磁盘可以在线自动扩展，也可以手动扩展，但是有需要注意的地方：
    * 只能扩展，不能收缩
    * 自动扩展的大小是max(5GB, 10%, FreeStorageSpace in 7hr)
    * 手动扩展至少要增加现有空间的10%
    * 每次扩展后会有6小时的冷却时间，过了6小时之后才能再次扩展。如果预期有大量数据插入，最好提前手动扩展出足够的空间，

* RDS PG的RDS的**pg_authid**表没有开放给用户，因此数据库的user信息无法导出。通过dump方法重建PG的时候，如果user不存在，user所属的object就无法创建。需要首先列出源上的user一览，然后在目标上重建user，才能通过dump文件恢复。

* RDS SQL Server的**mssqlsystemresource**里的**xp_fixeddrives**没有开放给用户，因此无法直接Native Backup/Restore。解决方法是使用自定义参数组，配置**SQL_SERVER_BACKUP_RESTORE**选项，配置角色和存放备份文件的S3存储桶，这样就可以使用SQL Server Management Studio的存储过程了。[参考页面](https://aws.amazon.com/cn/blogs/aws/amazon-rds-for-sql-server-support-for-native-backuprestore-to-amazon-s3/)。

---
### RDS参数组和选项组

RDS用[参数组](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/USER_WorkingWithParamGroups.html)来调整数据库引擎的参数，用[选项组](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/USER_WorkingWithOptionGroups.html)来控制数据库插件的行为。

默认参数组和默认选项组是不能修改的。如果想修改，必须自定义一个参数组或选项组，然后用自定义的组替换默认组。这个替换过程会造成RDS重启。

因此，建议所有RDS启动的时候都用**自定义参数组**和**自定义选项组**。这个自定义的组可以从默认组复制，需要的时候才修改内容，这样能减少RDS重启。

参数组中**可修改**项为**true**的参数都可以修改。应用类型为**dynamic**的参数修改不需要重启RDS，**static**的参数在重启后才能生效。

---
### RDS MySQL的空间占用
RDS MySQL的EBS上主要有以下对象会占用磁盘空间：
* 用户创建的内容
```sql
-- 用户创建的数据库
SELECT table_schema,
       ROUND(SUM(data_length+index_length)/1024/1024/1024,2) "size in GB"
FROM information_schema.tables
GROUP BY 1 ORDER BY 2 DESC;

-- 数据库碎片空间估值
SELECT table_schema AS "DB_NAME",
       SUM(size) "DB_SIZE",
       SUM(fragmented_space) APPROXIMATED_FRAGMENTED_SPACE_GB
FROM (SELECT table_schema, table_name, ROUND((data_length+index_length+data_free)/1024/1024/1024,2) AS size,
      ROUND((data_length-(AVG_ROW_LENGTH*TABLE_ROWS))/1024/1024/1024,2) AS fragmented_space
      FROM information_schema.tables
      WHERE table_type='BASE TABLE' AND
            table_schema NOT IN ('performance_schema', 'mysql', 'information_schema') ) AS TEMP
GROUP BY DB_NAME ORDER BY APPROXIMATED_FRAGMENTED_SPACE_GB DESC;

-- 表碎片空间估值
SELECT table_schema DB_NAME,
       table_name TABLE_NAME,
    ROUND((data_length+index_length+data_free)/1024/1024/1024,2) SIZE_GB,
    ROUND((data_length-(AVG_ROW_LENGTH*TABLE_ROWS))/1024/1024/1024,2) APPROXIMATED_FRAGMENTED_SPACE_GB
FROM information_schema.tables
WHERE table_type='BASE TABLE' AND
      table_schema NOT IN ('performance_schema', 'mysql', 'information_schema')
ORDER BY APPROXIMATED_FRAGMENTED_SPACE_GB DESC;

-- MySQL >=5.7， 查询information_schema更准确
-- 数据库碎片空间估值
SELECT SUBSTRING_INDEX(it.name, '/', 1) AS table_schema,
       ROUND(SUM(its.allocated_size)/1024/1024/1024,2) "size in GB",
       ROUND(SUM(t.data_free)/1024/1024/1024,2) "fragmented size in GB"
FROM information_schema.innodb_sys_tables it INNER JOIN
     information_schema.innodb_sys_tablespaces its
     ON it.space=its.space INNER JOIN
     information_schema.innodb_sys_tablestats istat
     ON istat.table_id=it.table_id INNER JOIN
     information_schema.tables t
     ON t.table_schema=SUBSTRING_INDEX(it.name, '/', 1) AND
        t.table_name=SUBSTRING_INDEX(it.name, '/', -1)
GROUP BY 1 ORDER BY 2 DESC;

-- MySQL >=5.7， 查询information_schema更准确
-- 表碎片空间估值
SELECT SUBSTRING_INDEX(it.name, '/', 1) AS table_schema,
       t.table_name,
       ROUND(its.allocated_size/1024/1024/1024,2) "size in GB",
       ROUND(t.data_free/1024/1024/1024,2) "fragmented size in GB"
FROM information_schema.innodb_sys_tables it INNER JOIN
     information_schema.innodb_sys_tablespaces its
     ON it.space=its.space INNER JOIN
     information_schema.innodb_sys_tablestats istat
     ON istat.table_id=it.table_id INNER JOIN
     information_schema.tables t
     ON t.table_schema=SUBSTRING_INDEX(it.name, '/', 1) AND
        t.table_name=SUBSTRING_INDEX(it.name, '/', -1)
WHERE t.table_schema NOT IN ('performance_schema', 'mysql', 'information_schema')
ORDER BY 4 DESC;
```
如果表的碎片较多，可以通过**OPTIMIZE TABLE tablename**来清理空间，但是清理过程中会**锁表**。
* binlog
```sql
-- 查看Master上的binlog
SHOW MASTER LOGS;
```
如果binlog占了比较多的空间，可以调整其保存的时间。
```sql
-- 查看binlog保存时间的配置
CALL mysql.rds_show_configuration;
-- 设置binlog保存24小时(0-168小时)
call mysql.rds_set_configuration('binlog retention hours', 24);
```
另外，如果Slave同步失败，有可能造成Master节点上binlog累积很多。同步完成后就不会累积了。
* 常规日志，慢查询日志
它们默认以表的形式保存，如果占用了太多空间，可以用下面的命令强制删除。
```sql
CALL mysql.rds_rotate_slow_log;
CALL mysql.rds_rotate_general_log;
```
* InnoDB日志和表空间等其它对象

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

