package com.example.order.feign;

import com.example.common.api.PayApi;
import org.springframework.cloud.openfeign.FeignClient;

@FeignClient(name = "pay-service")
public interface PayServiceClient extends PayApi {
}