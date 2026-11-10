package com.taobao.analysis.controller;

import com.taobao.analysis.common.ApiResult;
import com.taobao.analysis.service.AnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 数据看板模块：流量趋势、活跃时段、漏斗、路径、关联规则、Top 商品
 */
@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    private final AnalysisService service;

    public DashboardController(AnalysisService service) {
        this.service = service;
    }

    @GetMapping("/nov-pv-cum")
    public ApiResult<?> novPvCum() { return ApiResult.success(service.all("stat_nov_pv_cum")); }

    @GetMapping("/buy-cum")
    public ApiResult<?> buyCum() { return ApiResult.success(service.all("stat_buy_cum")); }

    @GetMapping("/hour")
    public ApiResult<?> hour() { return ApiResult.success(service.all("bp_hour")); }

    @GetMapping("/hour-weekday")
    public ApiResult<?> hourWeekday() { return ApiResult.success(service.all("bp_hour_weekday")); }

    @GetMapping("/weekday-avg")
    public ApiResult<?> weekdayAvg() { return ApiResult.success(service.all("bp_weekday_avg")); }

    @GetMapping("/top-pv")
    public ApiResult<?> topPv() { return ApiResult.success(service.all("bp_top10_pv_items")); }

    @GetMapping("/top-buy")
    public ApiResult<?> topBuy() { return ApiResult.success(service.all("bp_top10_buy_items")); }

    @GetMapping("/funnel")
    public ApiResult<?> funnel() { return ApiResult.success(service.all("bp_session_funnel")); }

    @GetMapping("/path-conversion")
    public ApiResult<?> pathConversion() { return ApiResult.success(service.all("bp_path_conversion")); }

    @GetMapping("/flow-edges")
    public ApiResult<?> flowEdges() { return ApiResult.success(service.all("bp_flow_edges")); }

    @GetMapping("/apriori")
    public ApiResult<?> apriori() { return ApiResult.success(service.top("bp_apriori_rules", "lift desc", 20)); }

    @GetMapping("/purchase-lag")
    public ApiResult<?> purchaseLag() { return ApiResult.success(service.all("bp_user_purchase_lag")); }

    @GetMapping("/category-rank")
    public ApiResult<?> categoryRank() { return ApiResult.success(service.top("stat_nov_user_category_rank", null, 20)); }

    @GetMapping("/top30-users")
    public ApiResult<?> top30Users() { return ApiResult.success(service.top("stat_top30_buy_users", null, 30)); }

    @GetMapping("/gap-dist")
    public ApiResult<?> gapDist() { return ApiResult.success(service.all("stat_buy_gap_dist")); }

    /** 看板页面一次性聚合 */
    @GetMapping("/all")
    public ApiResult<Map<String, Object>> all() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("novPvCum", service.all("stat_nov_pv_cum"));
        m.put("buyCum", service.all("stat_buy_cum"));
        m.put("hour", service.all("bp_hour"));
        m.put("hourWeekday", service.all("bp_hour_weekday"));
        m.put("weekdayAvg", service.all("bp_weekday_avg"));
        m.put("topPv", service.all("bp_top10_pv_items"));
        m.put("topBuy", service.all("bp_top10_buy_items"));
        m.put("funnel", service.all("bp_session_funnel"));
        m.put("pathConversion", service.all("bp_path_conversion"));
        m.put("flowEdges", service.all("bp_flow_edges"));
        m.put("apriori", service.top("bp_apriori_rules", "lift desc", 20));
        return ApiResult.success(m);
    }
}
