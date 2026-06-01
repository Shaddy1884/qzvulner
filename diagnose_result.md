
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  诊断设置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  查询: Tongweb安全漏洞
  search_depth: basic
  max_results: 10
  report_max_items: 6
  LLM model: deepseek-v4-flash
  LLM base_url: http://mirrors.shterm.com:4000/v1

════════════════════════════════════════════════════════════
  Stage 1 — 查询扩展
════════════════════════════════════════════════════════════
  硬编码 fallback: ['Tongweb安全漏洞']
  LLM 扩展 (5 条, 2.5s):
    • Tongweb 远程代码执行 RCE CVE CNVD 漏洞
    • Tongweb 反序列化漏洞 PoC Exploit-DB
    • Tongweb XSS SQL注入 文件上传 漏洞
    • Tongweb 官方安全公告 漏洞修复 补丁
    • Tongweb 中间件 漏洞 社区分析 安全研究

════════════════════════════════════════════════════════════
  Stage 2 — Tavily 原始搜索结果
════════════════════════════════════════════════════════════
  ✓ 'Tongweb 远程代码执行 RCE CVE CNVD 漏洞'  →  5 results
  ✓ 'Tongweb 反序列化漏洞 PoC Exploit-DB'  →  5 results
  ✓ 'Tongweb XSS SQL注入 文件上传 漏洞'  →  5 results
  ✓ 'Tongweb 官方安全公告 漏洞修复 补丁'  →  5 results
  ✓ 'Tongweb 中间件 漏洞 社区分析 安全研究'  →  5 results

  搜索总耗时: 8.8s

  ── Query 1: 'Tongweb 远程代码执行 RCE CVE CNVD 漏洞' (5 results) ──
  1. 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞 | CN-SEC 中文网
     来源: cn-sec.com
     链接: https://cn-sec.com/archives/1958325.html
     摘要: CN-SEC 中文网 CN-SEC 中文网. # 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞. 2023年8月20日*23:17:51**评论*2,346 views字数 668阅读2分13秒阅读模式. 影响版本：TW7.X≤7.0.4.9. 影响版本：7.0.4.6\_M3≤TW7.X≤7048\_M1. 问题描述：部分版本JMX服

  2. GitHub - Sec-Fork/POC-20250106: 收集整理漏洞EXP/POC,大部分漏洞来源网络，目前收集整理了1400多个poc/exp，长期更新。
     来源: github.com
     链接: https://github.com/Sec-Fork/POC-20250106
     摘要: *   [大华智能物联综合管理平台GetClassValue.jsp远程代码执行漏洞](https://github.com/Sec-Fork/POC-20250106/blob/main/%E5%A4%A7%E5%8D%8E/%E5%A4%A7%E5%8D%8E%E6%99%BA%E8%83%BD%E7%89%A9%E8%81%94%E7%BB%BC%E5

  3. TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244670.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244670.html 复制链接 复制链接. # TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）. 2

  4. TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244886.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244886.html 复制链接 复制链接. # TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）. 2

  5. TongWeb管理控制台存在命令执行漏洞（CNVD-2022-16268）
     来源: www.sxxdckj.com
     链接: https://www.sxxdckj.com/cms/a/TongWeb-guan-li-kong-zhi-tai-cun-zai-ming-ling-zhi-xing-lou-dong-CNVD-2022-16268.html
     摘要: TongWeb是北京东方通科技股份有限公司的一款应用服务器。 TongWeb管理控制台存在命令执行漏洞，攻击者可利用该漏洞获取服务器控制权限。


  ── Query 2: 'Tongweb 反序列化漏洞 PoC Exploit-DB' (5 results) ──
  1. 2023HW漏洞POC EXP、情报汇总知识库（动态更新） - Scribd
     来源: www.scribd.com
     链接: https://www.scribd.com/document/815429733/2023HW%E6%BC%8F%E6%B4%9EPOC-EXP-%E6%83%85%E6%8A%A5%E6%B1%87%E6%80%BB%E7%9F%A5%E8%AF%86%E5%BA%93-%E5%8A%A8%E6%80%81%E6%9B%B4%E6%96%B0
     摘要: BinaryFormatter 反序列化，因此可以用[Link] 来生成反序列化payload，再通过Soap 调用远程方法来触发反序列化，实现任意代码执行，从而导致服务器被接管。

  2. CVE-2024-34102 Magento XXE 漏洞分析 - Bmth's blog
     来源: www.bmth666.cn
     链接: http://www.bmth666.cn/2024/06/28/CVE-2024-34102-Magento-XXE-%E6%BC%8F%E6%B4%9E%E5%88%86%E6%9E%90/index.html
     摘要: 漏洞利用. POC已经公开了：https://raw.githubusercontent.com ... TongWeb ejbserver反序列化漏洞分析

  3. 2023HW漏洞POC/EXP - 树大招疯 - 博客园
     来源: www.cnblogs.com
     链接: https://www.cnblogs.com/dxmao/articles/17674294.html
     摘要: ### 1.1Panel后台存在任意文件读取漏洞. ### 3.Adobe ColdFusion 反序列化漏洞CVE-2023-29300. <string>ldap://xxx.xxx.xxx:1234/Basic/TomcatEcho</string>. matches: (code.eq("200") && body.contains("Index o

  4. 我是如何利用manager后台弱口令拿到服务器权限的 - CSDN文库
     来源: wenku.csdn.net
     链接: https://wenku.csdn.net/answer/545mof799p8
     摘要: # Java反序列化漏洞实战：利用AspectJWeaver实现任意文件写入与RCE 在Java应用安全领域，反序列化漏洞始终是攻防对抗的焦点。这类漏洞的威力在于

  5. SecBooks/SUMMARY.md at main · SexyBeast233/SecBooks
     来源: github.com
     链接: https://github.com/SexyBeast233/SecBooks/blob/main/SUMMARY.md
     摘要: # SecBooks/SUMMARY.md at main · SexyBeast233/SecBooks · GitHub. # SUMMARY.md. *   (CVE-2020-25078)D-Link DCS 系列监控 账号密码信息泄露漏洞D-Link%20DCS 系列监控 账号密码信息泄露漏洞.md). *   (CVE-2020-7961)Lif


  ── Query 3: 'Tongweb XSS SQL注入 文件上传 漏洞' (5 results) ──
  1. TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244886.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244886.html 复制链接 复制链接. # TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）. 2

  2. TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244670.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244670.html 复制链接 复制链接. # TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）. 2

  3. 2021护网公布漏洞清单- 网安客
     来源: www.wanganke.com
     链接: https://www.wanganke.com/web/article/show/11
     摘要: Nagios Network Analyzer | [Nagios Network Analyzer SQL 注入漏洞- CVE-2021-28925] ... TongWeb | [tongweb文件上传漏洞] |. 4月16日. Weblogic | [

  4. 关于tongweb任意文件上传高危漏洞的预警（SAL2021-B027） - CUBA - jmix.cn
     来源: forum.cuba-platform.cn
     链接: https://forum.cuba-platform.cn/t/topic/1748
     摘要: # 关于tongweb任意文件上传高危漏洞的预警（SAL2021-B027）. tongweb 管理后台存在不可见、不可更改密码的用户‘cli’，可绕过组件的身份认证，调用隐蔽的文件上传接口进行任意文件上传，上传路径为sysweb/upload。具体技术详情可参考附件。. CUBA Studio Version 6.7.1. Apache Tomcat Ve

  5. 野驴70/HW20210421Vul - Gitee
     来源: gitee.com
     链接: https://gitee.com/kiang70/HW20210421Vul
     摘要: Joomla XSS漏洞. 2021/04/15, TongWeb, tongweb文件上传漏洞. 2021/04/16, Weblogic, Weblogic T3 反序列化远程代码执行漏洞. 2021/04/16, 微信, 青藤捕获在野微信0day漏洞


  ── Query 4: 'Tongweb 官方安全公告 漏洞修复 补丁' (5 results) ──
  1. 东方通TongWeb应用服务器ejbserver远程代码执行漏洞风险通告 - 安全内参 | 决策者的网络安全知识库
     来源: www.secrss.com
     链接: https://www.secrss.com/articles/85030?app=1
     摘要: # 东方通TongWeb应用服务器ejbserver远程代码执行漏洞风险通告. 奇安信 CERT 2025-11-14. |  | 东方通 TongWeb 应用服务器 ejbserver 远程代码执行漏洞 |. | ****公开时间**** | 2025-11-05 | ****影响量级**** | 万级 |. | **奇安信评级** | **高危** |

  2. 【安全风险通告】东方通应用服务器Tongweb反序列化远程代码执行 ...
     来源: www.cup.edu.cn
     链接: https://www.cup.edu.cn/nic/wlaq/fd854ece782a47e1acda44e050fdb91d.htm
     摘要: <综合评定威胁等级>：严重，能执行任意代码。 官方解决方案：官方已发布补丁修复该漏洞，建议受影响用户更新以下补丁：https://www.tongtech.com/dft

  3. 【高危漏洞预警】东方通TongWeb ejbserver远程代码执行漏洞
     来源: www.xtcaq.com
     链接: http://www.xtcaq.com/nd.jsp?id=10231
     摘要: 漏洞描述: 东方通官方发布补丁修复了TongWeb应用服务器中存在的远程代码执行漏洞,该漏洞源于TongWeb默认开启的EJB远程服务存在安全缺陷,ejbserver接口在处理反序列化

  4. 东方通应用服务器EJB 反序列化远程代码执行漏洞 - CT Stack 安全社区
     来源: stack.chaitin.com
     链接: https://stack.chaitin.com/vuldb/detail/dcbf8e7f-9594-440e-8fed-05fc5191c0e8
     摘要: 2025年11月， 东方通官方发布补丁修复了长亭科技安全研究员发现的远程代码执行漏洞。TongWeb在处理EJP协议数据的时候，没有对请求的数据进行校验，导致攻击者

  5. AVD-2023-1700226 - 阿里云漏洞库
     来源: avd.aliyun.com
     链接: https://avd.aliyun.com/detail?id=AVD-2023-1700226
     摘要: TongWeb管理控制台存在命令执行漏洞，攻击者可利用该漏洞获取服务器控制权限。 解决建议. 供应商发布了安全公告及相关补丁信息，修复了此漏洞，建议用户下载使用：http://www.


  ── Query 5: 'Tongweb 中间件 漏洞 社区分析 安全研究' (5 results) ──
  1. TongWeb闭源中间件代码审计 - 知乎专栏
     来源: zhuanlan.zhihu.com
     链接: https://zhuanlan.zhihu.com/p/1920442831182476257
     摘要: 本文对该中间件部分公开在互联网，但未分析细节的漏洞，进行复现分析：. sysweb后台上传getshell：. 在互联网搜索发现该版本存在sysweb后台文件下载

  2. 东方通——构建安全智能的数字世界
     来源: www.tongtech.com
     链接: https://www.tongtech.com/pctype/114.html
     摘要: ## **安全可信应用服务器中间件TongWeb-T**. TongWeb-T是一款建立在原TongWeb核心技术基础之上的新一代的应用服务器中间件产品。通过引入先进的可信计算安全主动免疫防御技术和可信度算法技术等，使应用服务器中间具备了原生的安全防御能力。此外，这款产品还延续了TongWeb原有的优秀特性。. TongWeb-T在防御方式上采用的是双系统架

  3. tongweb | CN-SEC 中文网
     来源: cn-sec.com
     链接: http://cn-sec.com/archives/tag/tongweb
     摘要: CN-SEC 中文网 CN-SEC 中文网. ## TongWeb EJB反序列化RCE漏洞被动扫描插件. TongWeb应用服务器在处理EJB协议数据时未对请求进行校验，导致反序列化漏洞。攻击者可通过构造恶意数据在服务器执行任意代码。影响版本7.0.0.0至7.0.4.9及6.1.7.0至6.1.8.13... ## QVD-2025-44295：东方通T

  4. 分享技术，悦享品质 - 安全脉搏
     来源: www.secpulse.com
     链接: https://www.secpulse.com/page/44?lc6my=
     摘要: TongWeb闭源中间件代码审计. 应用服务器TongWeb v7 全面支持JavaEE7 及JavaEE8规范，作为基础架构软件，位于操作系统与应用之间，帮助企业将业务应用集成在一个基础平台

  5. 服务与支持-资料中心 - 东方通
     来源: www.tongtech.com
     链接: https://www.tongtech.com/download.html
     摘要: ## 用户登陆. * 东方通产品漏洞处置和安全加固流程  2024-06-12 14:51:54. * 消息中间件TongLINK/Q  2022-12-30 21:23:13. * 数据交换平台TongDXP  2022-12-30 21:22:21. * 数据集成处理工具TongETL  2022-08-17 13:45:21. * 企业服务总线软件To


════════════════════════════════════════════════════════════
  Stage 3 — 合并去重
════════════════════════════════════════════════════════════
  原始结果数: 25
  去重后结果: 23

  Tavily Answer:
    TongWeb has a remote code execution vulnerability (CVE CNVD) affecting certain versions, allowing attackers to gain control. The affected versions are TW7.X≤7.0.4.9 and TW6.X≤6.1.5.24. Patches are available from the vendor.
    - The generated text has been blocked by our content filters.
    TongWeb has vulnerabilities including XSS and SQL injection via file upload. A patch is available from the manufacturer. Critical updates should be applied promptly.
    TongWeb ejbserver had a remote code execution vulnerability patched in 2025; the exploit allowed attackers to execute arbitrary code; official patches are available from TongTech.
    TongWeb middleware has known vulnerabilities including remote code execution and file upload issues. The latest version addresses these security flaws. Official patches are available for affected versions.

  去重后结果列表:
  1. 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞 | CN-SEC 中文网
     来源: cn-sec.com
     链接: https://cn-sec.com/archives/1958325.html
     摘要: CN-SEC 中文网 CN-SEC 中文网. # 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞. 2023年8月20日*23:17:51**评论*2,346 views字数 668阅读2分13秒阅读模式. 影响版本：TW7.X≤7.0.4.9. 影响版本：7.0.4.6\_M3≤TW7.X≤7048\_M1. 问题描述：部分版本JMX服

  2. GitHub - Sec-Fork/POC-20250106: 收集整理漏洞EXP/POC,大部分漏洞来源网络，目前收集整理了1400多个poc/exp，长期更新。
     来源: github.com
     链接: https://github.com/Sec-Fork/POC-20250106
     摘要: *   [大华智能物联综合管理平台GetClassValue.jsp远程代码执行漏洞](https://github.com/Sec-Fork/POC-20250106/blob/main/%E5%A4%A7%E5%8D%8E/%E5%A4%A7%E5%8D%8E%E6%99%BA%E8%83%BD%E7%89%A9%E8%81%94%E7%BB%BC%E5

  3. TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244670.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244670.html 复制链接 复制链接. # TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）. 2

  4. TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244886.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244886.html 复制链接 复制链接. # TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）. 2

  5. TongWeb管理控制台存在命令执行漏洞（CNVD-2022-16268）
     来源: www.sxxdckj.com
     链接: https://www.sxxdckj.com/cms/a/TongWeb-guan-li-kong-zhi-tai-cun-zai-ming-ling-zhi-xing-lou-dong-CNVD-2022-16268.html
     摘要: TongWeb是北京东方通科技股份有限公司的一款应用服务器。 TongWeb管理控制台存在命令执行漏洞，攻击者可利用该漏洞获取服务器控制权限。

  6. 2023HW漏洞POC EXP、情报汇总知识库（动态更新） - Scribd
     来源: www.scribd.com
     链接: https://www.scribd.com/document/815429733/2023HW%E6%BC%8F%E6%B4%9EPOC-EXP-%E6%83%85%E6%8A%A5%E6%B1%87%E6%80%BB%E7%9F%A5%E8%AF%86%E5%BA%93-%E5%8A%A8%E6%80%81%E6%9B%B4%E6%96%B0
     摘要: BinaryFormatter 反序列化，因此可以用[Link] 来生成反序列化payload，再通过Soap 调用远程方法来触发反序列化，实现任意代码执行，从而导致服务器被接管。

  7. CVE-2024-34102 Magento XXE 漏洞分析 - Bmth's blog
     来源: www.bmth666.cn
     链接: http://www.bmth666.cn/2024/06/28/CVE-2024-34102-Magento-XXE-%E6%BC%8F%E6%B4%9E%E5%88%86%E6%9E%90/index.html
     摘要: 漏洞利用. POC已经公开了：https://raw.githubusercontent.com ... TongWeb ejbserver反序列化漏洞分析

  8. 2023HW漏洞POC/EXP - 树大招疯 - 博客园
     来源: www.cnblogs.com
     链接: https://www.cnblogs.com/dxmao/articles/17674294.html
     摘要: ### 1.1Panel后台存在任意文件读取漏洞. ### 3.Adobe ColdFusion 反序列化漏洞CVE-2023-29300. <string>ldap://xxx.xxx.xxx:1234/Basic/TomcatEcho</string>. matches: (code.eq("200") && body.contains("Index o

  9. 我是如何利用manager后台弱口令拿到服务器权限的 - CSDN文库
     来源: wenku.csdn.net
     链接: https://wenku.csdn.net/answer/545mof799p8
     摘要: # Java反序列化漏洞实战：利用AspectJWeaver实现任意文件写入与RCE 在Java应用安全领域，反序列化漏洞始终是攻防对抗的焦点。这类漏洞的威力在于

  10. SecBooks/SUMMARY.md at main · SexyBeast233/SecBooks
     来源: github.com
     链接: https://github.com/SexyBeast233/SecBooks/blob/main/SUMMARY.md
     摘要: # SecBooks/SUMMARY.md at main · SexyBeast233/SecBooks · GitHub. # SUMMARY.md. *   (CVE-2020-25078)D-Link DCS 系列监控 账号密码信息泄露漏洞D-Link%20DCS 系列监控 账号密码信息泄露漏洞.md). *   (CVE-2020-7961)Lif


════════════════════════════════════════════════════════════
  Stage 4 — LLM 相关性重排序
════════════════════════════════════════════════════════════
  重排序完成 (6 条, 4.7s):
  1. 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞 | CN-SEC 中文网
     来源: cn-sec.com
     链接: https://cn-sec.com/archives/1958325.html
     摘要: CN-SEC 中文网 CN-SEC 中文网. # 【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞. 2023年8月20日*23:17:51**评论*2,346 views字数 668阅读2分13秒阅读模式. 影响版本：TW7.X≤7.0.4.9. 影响版本：7.0.4.6\_M3≤TW7.X≤7048\_M1. 问题描述：部分版本JMX服
     评分: 9.5/10

  2. TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244670.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244670.html 复制链接 复制链接. # TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）. 2
     评分: 9.0/10

  3. TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778） | ZONE.CI 全球网
     来源: zone.ci
     链接: https://zone.ci/aliyun/ali_nonvd/244886.html
     摘要: # ZONE.CI 全球网 ZONE.CI 全球网. #### Plugins. #### WordPress. #### Web前端. #### 设计资源. https://zone.ci//aliyun/ali\_nonvd/244886.html 复制链接 复制链接. # TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）. 2
     评分: 9.0/10

  4. TongWeb管理控制台存在命令执行漏洞（CNVD-2022-16268）
     来源: www.sxxdckj.com
     链接: https://www.sxxdckj.com/cms/a/TongWeb-guan-li-kong-zhi-tai-cun-zai-ming-ling-zhi-xing-lou-dong-CNVD-2022-16268.html
     摘要: TongWeb是北京东方通科技股份有限公司的一款应用服务器。 TongWeb管理控制台存在命令执行漏洞，攻击者可利用该漏洞获取服务器控制权限。
     评分: 8.5/10

  5. 关于tongweb任意文件上传高危漏洞的预警（SAL2021-B027） - CUBA - jmix.cn
     来源: forum.cuba-platform.cn
     链接: https://forum.cuba-platform.cn/t/topic/1748
     摘要: # 关于tongweb任意文件上传高危漏洞的预警（SAL2021-B027）. tongweb 管理后台存在不可见、不可更改密码的用户‘cli’，可绕过组件的身份认证，调用隐蔽的文件上传接口进行任意文件上传，上传路径为sysweb/upload。具体技术详情可参考附件。. CUBA Studio Version 6.7.1. Apache Tomcat Ve
     评分: 7.5/10

  6. 2021护网公布漏洞清单- 网安客
     来源: www.wanganke.com
     链接: https://www.wanganke.com/web/article/show/11
     摘要: Nagios Network Analyzer | [Nagios Network Analyzer SQL 注入漏洞- CVE-2021-28925] ... TongWeb | [tongweb文件上传漏洞] |. 4月16日. Weblogic | [
     评分: 6.0/10


════════════════════════════════════════════════════════════
  Stage 5 — LLM 聚合报告
════════════════════════════════════════════════════════════
  生成完成 (6.5s)

────────────────────────────────────────────────────────────
联网搜索：Tongweb安全漏洞
结论：东方通TongWeb存在多个高危漏洞，包括远程代码执行、命令执行和文件上传，影响TW6.X和TW7.X系列版本，厂商已发布补丁。

1. 标题：【攻防演练】东方通 TongWeb 应用服务器存在远程代码执行漏洞
   来源：cn-sec.com
   链接：https://cn-sec.com/archives/1958325.html
   摘要：TW7.X≤7.0.4.9及TW6.X≤6.1.5.24版本存在远程代码执行漏洞。

2. 标题：TongWeb管理控制台存在命令执行漏洞（CNVD-2021-49119）
   来源：zone.ci
   链接：https://zone.ci/aliyun/ali_nonvd/244670.html
   摘要：CNVD收录，攻击者可利用该漏洞获取服务器控制权限。

3. 标题：TongWeb管理控制台存在文件上传漏洞（CNVD-2021-24778）
   来源：zone.ci
   链接：https://zone.ci/aliyun/ali_nonvd/244886.html
   摘要：CNVD收录，管理控制台存在文件上传漏洞，厂商已提供修补方案。

4. 标题：TongWeb管理控制台存在命令执行漏洞（CNVD-2022-16268）
   来源：sxxdckj.com
   链接：https://www.sxxdckj.com/cms/a/TongWeb-guan-li-kong-zhi-tai-cun-zai-ming-ling-zhi-xing-lou-dong-CNVD-2022-16268.html
   摘要：攻击者可利用该漏洞获取服务器控制权限。

5. 标题：关于tongweb任意文件上传高危漏洞的预警（SAL2021-B027）
   来源：forum.cuba-platform.cn
   链接：https://forum.cuba-platform.cn/t/topic/1748
   摘要：后台存在隐藏用户‘cli’，可绕过认证上传任意文件至sysweb/upload。

6. 标题：2021护网公布漏洞清单
   来源：wanganke.com
   链接：https://www.wanganke.com/web/article/show/11
   摘要：护网行动公布清单中包含tongweb文件上传漏洞。
────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  耗时汇总
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    expand: 2.5s
    search: 8.8s
    rerank: 4.7s
    report: 6.5s
     TOTAL: 22.5s