package com.example.order.controller;

import com.example.common.api.OrderApi;
import com.example.common.dto.OrderDTO;
import com.example.order.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;

@RestController
public class OrderController implements OrderApi {

    @Autowired
    private OrderService orderService;

    @Override
    public List<OrderDTO> list() {
        return orderService.listAll();
    }

    @Override
    public OrderDTO getById(Long id) {
        return orderService.getById(id);
    }

    @Override
    public OrderDTO create(@RequestBody OrderDTO order) {
        return orderService.create(order.getUserId(), order.getAmount());
    }

    @PostMapping("/api/orders/{id}/pay")
    public OrderDTO pay(@PathVariable Long id) {
        return orderService.pay(id);
    }
}