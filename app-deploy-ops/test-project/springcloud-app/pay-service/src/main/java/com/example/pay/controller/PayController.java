package com.example.pay.controller;

import com.example.common.api.PayApi;
import com.example.common.dto.PayDTO;
import com.example.pay.service.PayService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PayController implements PayApi {

    @Autowired
    private PayService payService;

    @Override
    public PayDTO create(PayDTO pay) {
        return payService.create(pay);
    }

    @Override
    public PayDTO getByOrderId(Long orderId) {
        return payService.getByOrderId(orderId);
    }
}