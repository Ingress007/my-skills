package com.example.order.service;

import com.example.common.dto.OrderDTO;
import com.example.common.dto.PayDTO;
import com.example.common.dto.UserDTO;
import com.example.order.dao.OrderMapper;
import com.example.order.entity.Order;
import com.example.order.feign.PayServiceClient;
import com.example.order.feign.UserServiceClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class OrderService {

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private UserServiceClient userServiceClient;

    @Autowired
    private PayServiceClient payServiceClient;

    public List<OrderDTO> listAll() {
        return orderMapper.selectList(null).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public OrderDTO getById(Long id) {
        Order order = orderMapper.selectById(id);
        return order != null ? toDTO(order) : null;
    }

    public OrderDTO create(Long userId, BigDecimal amount) {
        // 验证用户存在（通过 Feign 调用 user-service）
        UserDTO user = userServiceClient.getById(userId);
        if (user == null) {
            throw new RuntimeException("User not found: " + userId);
        }

        Order order = new Order();
        order.setUserId(userId);
        order.setOrderNo(UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase());
        order.setAmount(amount);
        order.setStatus(0);
        order.setCreatedAt(LocalDateTime.now());
        order.setUpdatedAt(LocalDateTime.now());
        orderMapper.insert(order);
        return toDTO(order);
    }

    public OrderDTO pay(Long orderId) {
        Order order = orderMapper.selectById(orderId);
        if (order == null) {
            throw new RuntimeException("Order not found: " + orderId);
        }

        // 调用 pay-service 创建支付记录
        PayDTO payReq = new PayDTO();
        payReq.setOrderId(orderId);
        payReq.setAmount(order.getAmount());
        PayDTO payResult = payServiceClient.create(payReq);

        // 更新订单状态
        order.setStatus(1);
        order.setUpdatedAt(LocalDateTime.now());
        orderMapper.updateById(order);

        return toDTO(order);
    }

    private OrderDTO toDTO(Order order) {
        OrderDTO dto = new OrderDTO();
        dto.setId(order.getId());
        dto.setUserId(order.getUserId());
        dto.setOrderNo(order.getOrderNo());
        dto.setAmount(order.getAmount());
        dto.setStatus(order.getStatus());
        dto.setCreatedAt(order.getCreatedAt());
        return dto;
    }
}