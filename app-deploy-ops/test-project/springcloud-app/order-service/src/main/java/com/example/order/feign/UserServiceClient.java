package com.example.order.feign;

import com.example.common.api.UserApi;
import org.springframework.cloud.openfeign.FeignClient;

@FeignClient(name = "user-service")
public interface UserServiceClient extends UserApi {
}