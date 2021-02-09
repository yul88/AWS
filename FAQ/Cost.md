# Cost
概述TBD

### 监控Metric指标

---
### 选择合适的价格模型
价格模型 | 特点
:---|:---
按需实例(On Demand) | 按秒计费，无折扣
预留实例(Reserved) | OD的6-7折，连续包1年或3年
竞价实例(On Spot) | OD的1-2折，计算资源可能被回收

免费Linux的EC2的预留实例大部分都支持[实例大小灵活匹配](https://docs.aws.amazon.com/whitepapers/latest/cost-optimization-reservation-models/maximizing-utilization-with-size-flexibility-in-regional-reserved-instances.html)，比如:

* 比如1个m5.xlarge的RI可以匹配2个m5.large的EC2
* 比如4个c5.large的RI可以匹配1个c5.2xlarge的EC2

注意：
* Windows实例，Redhat/SUSE Linux实例，G4实例，专用主机，指定可用区的RI，它们不支持灵活匹配。
* ElasticSearch，ElastiCache, RDS SQL Server不支持灵活匹配。

---
### 选择合适的EC2类型


---
### 利用弹性伸缩

---
### 选择合适类型的存储和数据库

