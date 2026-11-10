package com.taobao.analysis;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 淘宝用户购物行为大数据分析系统 - 后端启动类
 */
@SpringBootApplication
public class TaobaoAnalysisApplication {
    public static void main(String[] args) {
        SpringApplication.run(TaobaoAnalysisApplication.class, args);
        System.out.println("==== 淘宝用户行为分析系统后端启动成功: http://localhost:8080 ====");
    }
}
