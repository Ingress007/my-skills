package com.example.pay.service;

import com.example.common.dto.PayDTO;
import com.example.pay.dao.PayRecordMapper;
import com.example.pay.entity.PayRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class PayService {

    @Autowired
    private PayRecordMapper payRecordMapper;

    public PayDTO create(PayDTO dto) {
        PayRecord record = new PayRecord();
        record.setOrderId(dto.getOrderId());
        record.setPayNo("PAY" + UUID.randomUUID().toString().replace("-", "").substring(0, 14).toUpperCase());
        record.setAmount(dto.getAmount());
        record.setPayStatus(1); // 模拟直接支付成功
        record.setCreatedAt(LocalDateTime.now());
        record.setUpdatedAt(LocalDateTime.now());
        payRecordMapper.insert(record);
        return toDTO(record);
    }

    public PayDTO getByOrderId(Long orderId) {
        // 使用 QueryWrapper 按 orderId 查询
        PayRecord record = payRecordMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<PayRecord>()
                        .eq("order_id", orderId)
        );
        return record != null ? toDTO(record) : null;
    }

    private PayDTO toDTO(PayRecord record) {
        PayDTO dto = new PayDTO();
        dto.setId(record.getId());
        dto.setOrderId(record.getOrderId());
        dto.setPayNo(record.getPayNo());
        dto.setAmount(record.getAmount());
        dto.setPayStatus(record.getPayStatus());
        dto.setCreatedAt(record.getCreatedAt());
        return dto;
    }
}