package com.example.common.api;

import com.example.common.dto.OrderDTO;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RequestMapping("/api/orders")
public interface OrderApi {

    @GetMapping
    List<OrderDTO> list();

    @GetMapping("/{id}")
    OrderDTO getById(@PathVariable("id") Long id);

    @PostMapping
    OrderDTO create(@RequestBody OrderDTO order);
}