package com.energy;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;

import java.io.IOException;
import java.io.OutputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * Enterprise Java Energy Compliance & ISO 50001 EnPI Microservice.
 * Demonstrates high-performance Java backend calculation engine
 * for industrial power quality compliance and multi-tier energy billing.
 */
public class EnergyComplianceApplication {

    private static final int PORT = 8081;

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        
        server.createContext("/api/compliance/health", new HealthHandler());
        server.createContext("/api/compliance/iso50001", new ISO50001ComplianceHandler());
        server.createContext("/api/compliance/tariff-audit", new TariffAuditHandler());
        
        server.setExecutor(null); // default executor
        System.out.println("=================================================");
        System.out.println(" Java Energy Compliance Microservice started!");
        System.out.println(" Listening on http://localhost:" + PORT);
        System.out.println(" - Health:     http://localhost:" + PORT + "/api/compliance/health");
        System.out.println(" - ISO 50001:  http://localhost:" + PORT + "/api/compliance/iso50001?kwh=5000&peakKw=150&pf=0.92");
        System.out.println("=================================================");
        server.start();
    }

    static class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCorsHeaders(exchange);
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(204, -1);
                return;
            }
            String response = "{\"status\":\"UP\",\"service\":\"Java-ISO50001-Compliance-Engine\",\"version\":\"2.4.0\",\"runtime\":\"Java " + System.getProperty("java.version") + "\"}";
            sendJsonResponse(exchange, 200, response);
        }
    }

    static class ISO50001ComplianceHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCorsHeaders(exchange);
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(204, -1);
                return;
            }

            Map<String, String> queryParams = parseQueryParams(exchange.getRequestURI().getQuery());
            double kwh = parseDouble(queryParams.get("kwh"), 4500.0);
            double peakKw = parseDouble(queryParams.get("peakKw"), 160.0);
            double pf = parseDouble(queryParams.get("pf"), 0.93);

            // ISO 50001 Energy Performance Indicator (EnPI)
            double loadFactor = (kwh / (peakKw * 24.0)) * 100.0;
            loadFactor = Math.min(100.0, Math.max(0.0, loadFactor));

            boolean pfCompliant = pf >= 0.85;
            double pfPenaltyPercent = pf < 0.85 ? ((0.85 - pf) * 100.0 * 1.5) : 0.0;
            
            String complianceGrade;
            if (pf >= 0.95 && loadFactor > 60) {
                complianceGrade = "ISO-50001-GOLD";
            } else if (pf >= 0.90 && loadFactor > 45) {
                complianceGrade = "ISO-50001-SILVER";
            } else if (pfCompliant) {
                complianceGrade = "ISO-50001-STANDARD";
            } else {
                complianceGrade = "NON-COMPLIANT-PENALTY";
            }

            double co2Kg = kwh * 0.42; // GHG Protocol factor

            String jsonResponse = String.format(
                "{" +
                "\"standard\":\"ISO 50001:2018 Energy Management\"," +
                "\"complianceGrade\":\"%s\"," +
                "\"loadFactorPct\":%.2f," +
                "\"powerFactor\":%.3f," +
                "\"isPfCompliant\":%b," +
                "\"penaltySurgePct\":%.2f," +
                "\"totalEnergyKwh\":%.2f," +
                "\"carbonEmissionsKg\":%.2f," +
                "\"enpiIndex\":%.3f," +
                "\"status\":\"APPROVED\"" +
                "}",
                complianceGrade, loadFactor, pf, pfCompliant, pfPenaltyPercent, kwh, co2Kg, (kwh / (peakKw + 1.0))
            );

            sendJsonResponse(exchange, 200, jsonResponse);
        }
    }

    static class TariffAuditHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            addCorsHeaders(exchange);
            if ("OPTIONS".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(204, -1);
                return;
            }

            // Industrial Tariff Breakdown
            String response = "{" +
                "\"tariffScheme\":\"Industrial High-Tension Time-of-Use\"," +
                "\"peakHours\":\"08:00 - 20:00\"," +
                "\"peakRatePerKwh\":0.18," +
                "\"offPeakRatePerKwh\":0.08," +
                "\"demandChargePerKw\":12.50," +
                "\"currency\":\"USD\"," +
                "\"recommendations\":[" +
                "\"Shift energy-intensive batch processing to off-peak night window (20:00-08:00).\"," +
                "\"Maintain APFC banks online to avoid low power factor utility surcharge.\"" +
                "]" +
                "}";

            sendJsonResponse(exchange, 200, response);
        }
    }

    private static void addCorsHeaders(HttpExchange exchange) {
        exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
        exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type, Authorization");
    }

    private static void sendJsonResponse(HttpExchange exchange, int statusCode, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static Map<String, String> parseQueryParams(String query) {
        Map<String, String> params = new HashMap<>();
        if (query == null || query.isEmpty()) return params;
        for (String param : query.split("&")) {
            String[] pair = param.split("=");
            if (pair.length > 1) {
                params.put(pair[0], pair[1]);
            } else if (pair.length == 1) {
                params.put(pair[0], "");
            }
        }
        return params;
    }

    private static double parseDouble(String val, double defaultVal) {
        if (val == null || val.trim().isEmpty()) return defaultVal;
        try {
            return Double.parseDouble(val.trim());
        } catch (NumberFormatException e) {
            return defaultVal;
        }
    }
}
