package com.taobao.analysis.controller;

import com.taobao.analysis.common.ApiResult;
import com.taobao.analysis.service.AnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 总览模块：核心 KPI 指标与每日概览
 */
@RestController
@RequestMapping("/api/overview")
public class OverviewController {

    private final AnalysisService service;

    public OverviewController(AnalysisService service) {
        this.service = service;
    }

    /** 核心指标（清洗规模、购买、RFM、XGBoost、ALS 等汇总） */
    @GetMapping("/metrics")
    public ApiResult<Map<String, Object>> metrics() {
        return ApiResult.success(service.metrics());
    }

    /** 每日概览（PV/UV/各行为） */
    @GetMapping("/daily")
    public ApiResult<?> daily() {
        return ApiResult.success(service.all("daily_overview"));
    }

    /** 行为类型占比 */
    @GetMapping("/behavior-ratio")
    public ApiResult<?> behaviorRatio() {
        return ApiResult.success(service.all("bp_behavior_ratio"));
    }

    /** 大屏首屏一次性返回总览所需数据 */
    @GetMapping("/screen")
    public ApiResult<Map<String, Object>> screen() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("metrics", service.metrics());
        m.put("daily", service.all("daily_overview"));
        m.put("behaviorRatio", service.all("bp_behavior_ratio"));
        return ApiResult.success(m);
    }
}
