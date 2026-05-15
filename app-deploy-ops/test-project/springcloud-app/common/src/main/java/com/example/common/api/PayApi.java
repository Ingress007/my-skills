package com.example.common.api;

import com.example.common.dto.PayDTO;
import org.springframework.web.bind.annotation.*;

@RequestMapping("/api/pays")
public interface PayApi {

    @PostMapping("/create")
    PayDTO create(@RequestBody PayDTO pay);

    @GetMapping("/order/{orderId}")
    PayDTO getByOrderId(@PathVariable("orderId") Long orderId);
}