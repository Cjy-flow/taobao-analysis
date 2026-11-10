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
 * RFM 用户分群模块：分群概览、八分法、明细分页
 */
@RestController
@RequestMapping("/api/rfm")
public class RfmController {

    private final AnalysisService service;

    public RfmController(AnalysisService service) {
        this.service = service;
    }

    /** K-Means 分群汇总 */
    @GetMapping("/cluster-summary")
    public ApiResult<?> clusterSummary() {
        return ApiResult.success(service.all("rfm_cluster_summary"));
    }

    /** RFM 八分法汇总 */
    @GetMapping("/octant")
    public ApiResult<?> octant() {
        return ApiResult.success(service.all("rfm_octant_summary"));
    }

    /** 明细分页，可按分群 cluster 过滤 */
    @GetMapping("/detail")
    public ApiResult<Map<String, Object>> detail(
            @RequestParam(required = false) Integer cluster,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        Map<String, Object> res = service.page("rfm_detail",
                cluster == null ? null : "cluster", cluster,
                "r_score desc, f_score desc, m_score desc", page, size);
        return ApiResult.success(res);
    }

    /** R-F 四象限散点（全量明细，供散点图） */
    @GetMapping("/scatter")
    public ApiResult<?> scatter() {
        return ApiResult.success(service.all("rfm_detail"));
    }

    /** 分群页面聚合 */
    @GetMapping("/all")
    public ApiResult<Map<String, Object>> all() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("clusterSummary", service.all("rfm_cluster_summary"));
        m.put("octant", service.all("rfm_octant_summary"));
        return ApiResult.success(m);
    }
}
