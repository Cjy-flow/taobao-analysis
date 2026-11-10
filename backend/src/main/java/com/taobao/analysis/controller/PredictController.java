package com.taobao.analysis.controller;

import com.taobao.analysis.common.ApiResult;
import com.taobao.analysis.service.AnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 预测模型模块：XGBoost 购买意向预测、ALS 协同过滤推荐
 */
@RestController
@RequestMapping("/api/predict")
public class PredictController {

    private final AnalysisService service;

    public PredictController(AnalysisService service) {
        this.service = service;
    }

    // ---------- XGBoost ----------
    @GetMapping("/xgb-metrics")
    public ApiResult<?> xgbMetrics() { return ApiResult.success(service.all("xgb_metrics")); }

    @GetMapping("/xgb-confusion")
    public ApiResult<?> xgbConfusion() { return ApiResult.success(service.all("xgb_confusion")); }

    @GetMapping("/xgb-feature")
    public ApiResult<?> xgbFeature() { return ApiResult.success(service.all("xgb_feature_importance")); }

    @GetMapping("/xgb-roc")
    public ApiResult<?> xgbRoc() { return ApiResult.success(service.all("xgb_roc")); }

    /** 高购买意向用户排行榜分页 */
    @GetMapping("/xgb-rank")
    public ApiResult<Map<String, Object>> xgbRank(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ApiResult.success(service.page("xgb_predict_rank", null, null, "rank asc", page, size));
    }

    // ---------- ALS ----------
    @GetMapping("/als-metrics")
    public ApiResult<?> alsMetrics() { return ApiResult.success(service.all("als_metrics")); }

    @GetMapping("/als-popular")
    public ApiResult<?> alsPopular() { return ApiResult.success(service.all("als_popular_items")); }

    /** 某用户的个性化推荐 */
    @GetMapping("/als-recs")
    public ApiResult<?> alsRecs(@RequestParam Long userId) {
        return ApiResult.success(service.byColumn("als_user_recs", "user_id", userId, 10));
    }

    /** 预测模型页面聚合（不含分页明细） */
    @GetMapping("/all")
    public ApiResult<Map<String, Object>> all() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("xgbMetrics", service.all("xgb_metrics"));
        m.put("xgbConfusion", service.all("xgb_confusion"));
        m.put("xgbFeature", service.all("xgb_feature_importance"));
        m.put("xgbRoc", service.all("xgb_roc"));
        m.put("alsMetrics", service.all("als_metrics"));
        m.put("alsPopular", service.all("als_popular_items"));
        return ApiResult.success(m);
    }
}
