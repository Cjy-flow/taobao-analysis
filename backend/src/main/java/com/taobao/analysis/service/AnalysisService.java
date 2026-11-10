package com.taobao.analysis.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 分析结果读取服务：统一从 MySQL 读取 Spark 作业产出的结果表。
 * 表名通过白名单校验，避免 SQL 注入。
 */
@Service
public class AnalysisService {

    private final JdbcTemplate jdbc;

    /** 允许被接口访问的结果表白名单 */
    private static final Set<String> ALLOWED = Set.of(
            "daily_overview", "stat_nov_pv_cum", "stat_buy_cum",
            "stat_nov_user_category_rank", "stat_top30_buy_users", "stat_buy_gap_dist",
            "bp_behavior_ratio", "bp_hour", "bp_hour_weekday", "bp_weekday_avg",
            "bp_user_purchase_lag", "bp_top10_pv_items", "bp_top10_buy_items",
            "bp_session_funnel", "bp_path_conversion", "bp_flow_edges", "bp_apriori_rules",
            "rfm_detail", "rfm_cluster_summary", "rfm_octant_summary",
            "xgb_metrics", "xgb_confusion", "xgb_feature_importance", "xgb_roc", "xgb_predict_rank",
            "als_metrics", "als_user_recs", "als_popular_items", "analysis_metrics"
    );

    /** 时序/序列结果表的默认排序（MySQL 不保证返回顺序，图表必须按轴有序） */
    private static final Map<String, String> DEFAULT_ORDER = new HashMap<>();
    static {
        DEFAULT_ORDER.put("daily_overview", "`date` asc");
        DEFAULT_ORDER.put("stat_nov_pv_cum", "`date` asc");
        DEFAULT_ORDER.put("stat_buy_cum", "`date` asc");
        DEFAULT_ORDER.put("bp_hour", "`hour` asc");
        DEFAULT_ORDER.put("bp_hour_weekday", "`weekday` asc, `hour` asc");
        DEFAULT_ORDER.put("bp_weekday_avg", "`weekday` asc");
        DEFAULT_ORDER.put("bp_session_funnel", "`sessions` desc");
        DEFAULT_ORDER.put("bp_path_conversion", "`sessions` desc");
        DEFAULT_ORDER.put("bp_flow_edges", "`source` asc");
        DEFAULT_ORDER.put("xgb_roc", "`fpr` asc, `tpr` asc");
        DEFAULT_ORDER.put("xgb_feature_importance", "`gain` desc");
        DEFAULT_ORDER.put("als_user_recs", "`user_id` asc, `rank` asc");
        DEFAULT_ORDER.put("rfm_detail", "`user_id` asc");
        DEFAULT_ORDER.put("stat_nov_user_category_rank", "`dense_rk` asc, `rn` asc");
        DEFAULT_ORDER.put("stat_top30_buy_users", "`rn` asc");
        DEFAULT_ORDER.put("stat_buy_gap_dist", "`max_gap` asc");
    }

    private String defaultOrder(String table) {
        String o = DEFAULT_ORDER.get(table);
        return o == null ? "" : " ORDER BY " + o;
    }

    public AnalysisService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    private void check(String table) {
        if (table == null || !ALLOWED.contains(table)) {
            throw new IllegalArgumentException("非法或未授权的数据表: " + table);
        }
    }

    /** 规范化 ORDER BY：逐列加反引号（规避 rank 等保留字），支持多列；非法返回 null */
    private static final Pattern ORDER_PART = Pattern.compile("^([a-zA-Z0-9_]+)(\\s+(asc|desc))?$", Pattern.CASE_INSENSITIVE);
    private String normalizeOrder(String orderBy) {
        if (orderBy == null || orderBy.isBlank()) {
            return null;
        }
        StringBuilder sb = new StringBuilder();
        for (String part : orderBy.split(",")) {
            Matcher m = ORDER_PART.matcher(part.trim());
            if (!m.matches()) {
                return null;
            }
            if (sb.length() > 0) {
                sb.append(", ");
            }
            sb.append('`').append(m.group(1)).append('`');
            if (m.group(3) != null) {
                sb.append(' ').append(m.group(3).toLowerCase());
            }
        }
        return sb.length() == 0 ? null : sb.toString();
    }

    /** 全表读取 */
    public List<Map<String, Object>> all(String table) {
        check(table);
        return jdbc.queryForList("SELECT * FROM `" + table + "`" + defaultOrder(table));
    }

    /** 排序 + 限量读取 */
    public List<Map<String, Object>> top(String table, String orderBy, int limit) {
        check(table);
        int n = Math.min(Math.max(limit, 1), 5000);
        String sql = "SELECT * FROM `" + table + "`";
        String no = normalizeOrder(orderBy);
        if (no != null) {
            sql += " ORDER BY " + no;
        }
        sql += " LIMIT " + n;
        return jdbc.queryForList(sql);
    }

    /** 等值条件查询 */
    public List<Map<String, Object>> byColumn(String table, String column, Object value, int limit) {
        check(table);
        if (!column.matches("[a-zA-Z0-9_]+")) {
            throw new IllegalArgumentException("非法列名: " + column);
        }
        int n = Math.min(Math.max(limit, 1), 5000);
        return jdbc.queryForList(
                "SELECT * FROM `" + table + "` WHERE `" + column + "` = ?" + defaultOrder(table) + " LIMIT " + n, value);
    }

    /** 分页查询：返回 {total, rows} */
    public Map<String, Object> page(String table, String column, Object value,
                                    String orderBy, int page, int size) {
        check(table);
        int s = Math.min(Math.max(size, 1), 200);
        int p = Math.max(page, 1);
        int offset = (p - 1) * s;
        StringBuilder where = new StringBuilder();
        Object[] args = new Object[0];
        if (column != null && column.matches("[a-zA-Z0-9_]+") && value != null) {
            where.append(" WHERE `").append(column).append("` = ?");
            args = new Object[]{value};
        }
        Long total = jdbc.queryForObject(
                "SELECT COUNT(*) FROM `" + table + "`" + where, Long.class, args);
        String sql = "SELECT * FROM `" + table + "`" + where;
        String no = normalizeOrder(orderBy);
        if (no != null) {
            sql += " ORDER BY " + no;
        }
        sql += " LIMIT " + offset + "," + s;
        List<Map<String, Object>> rows = jdbc.queryForList(sql, args);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total", total);
        result.put("page", p);
        result.put("size", s);
        result.put("rows", rows);
        return result;
    }

    /** 汇总指标：metric -> value */
    public Map<String, Object> metrics() {
        List<Map<String, Object>> rows =
                jdbc.queryForList("SELECT metric, value, note FROM analysis_metrics");
        Map<String, Object> map = new LinkedHashMap<>();
        for (Map<String, Object> r : rows) {
            map.put(String.valueOf(r.get("metric")), r.get("value"));
        }
        return map;
    }
}
