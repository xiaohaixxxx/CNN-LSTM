from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import torch
from utils.utils import *
from datetime import datetime


# 训练器函数
def train_epoch(config, model, criterion, optimizer,data_loader, epoch):
    print('#'*60)
    print('Epoch {}. Starting with training phase.'.format(epoch+1))
    model.train()  #在训练开始之前写上 model.trian() ，在测试时写上 model.eval()
                    # 如果模型中有BN层（Batch Normalization）和 Dropout ，需要在 训练时 添加 model.train()
    # Epoch statistics
    steps_in_epoch = int(np.ceil(len(data_loader.dataset)/config.batch_size))   # steps 大小，batch_size越大，训练越快
    losses = np.zeros(steps_in_epoch, np.float32)                               # loss，每步记录一下
    accuracies = np.zeros(steps_in_epoch, np.float32)                           # 每步的正确率
    epoch_start_time = time.time()                                              # 开始时间
    for step, (clips, targets) in enumerate(data_loader):  #enumerate()函数用于将一个可遍历的数据对象
        start_time = time.time()
        optimizer.zero_grad()   #梯度初始化为零
        # GPU化
        clips=clips.permute(2, 0, 1, 3, 4)              # 维度换
        clips = clips.cuda()
        targets = targets.cuda()
        logits = model.forward(clips) # 获取logits
        #logits= logits[:,-1,:]   # lstm最后隐藏层的结果
        logits = torch.mean(logits,dim=1)                       # 取均值
        # 检测维度
        if epoch == 0 and step == 0:
            if logits.shape[1] != config.num_classes:
                raise RuntimeError('Number of output logits ({}) does not match number of classes ({})'.format(logits.shape[1], config.finetune_num_classes))
        _, preds = torch.max(logits, 1)                                        # 识别结果
       

        loss = criterion(logits, targets)                                      # loss函数
        # 计算准确率
        correct = torch.sum(preds == targets.data)
        accuracy = correct.double() / config.batch_size
        # 一秒内可以识别的样本
        examples_per_second = config.batch_size/float(time.time() - start_time)
        # 更新梯度
        loss.backward()
        optimizer.step()
        # 保存结果
        accuracies[step] = accuracy.item()
        losses[step] = loss.item()
        # 计算总共的步数
        global_step = (epoch*steps_in_epoch) + step
        # 每多少步进行输出
        if step % config.print_frequency == 0:
            print("[{}] Epoch {}. Train Step {:04d}/{:04d}, Examples/Sec = {:.2f}, "
                  "LR = {:.4f}, Accuracy = {:.3f}, Loss = {:.3f}".format(
                    datetime.now().strftime("%A %H:%M"), epoch+1,
                    step, steps_in_epoch, examples_per_second,
                    current_learning_rate(optimizer), accuracies[step], losses[step]))
    # 每个epoch的统计
    epoch_duration = float(time.time() - epoch_start_time)
    epoch_avg_loss = np.mean(losses)
    epoch_avg_acc  = np.mean(accuracies)
    return epoch_avg_loss, epoch_avg_acc, epoch_duration


# 验证器函数
def validation_epoch(config, model, criterion,data_loader, epoch):

    print('#'*60)
    print('Epoch {}. Starting with validation phase.'.format(epoch+1))
    model.eval()
    steps_in_epoch = int(np.ceil(len(data_loader.dataset)/config.batch_size))
    losses = np.zeros(steps_in_epoch, np.float32)
    accuracies = np.zeros(steps_in_epoch, np.float32)
    epoch_start_time = time.time()
    for step, (clips, targets) in enumerate(data_loader):
        start_time = time.time()
        clips=clips.permute(2, 0, 1, 3, 4)              # test ????????????????
        clips   = clips.cuda()
        targets = targets.cuda()
        logits = model.forward(clips)
        #logits= logits[:,-1,:]   # lstm最后隐藏层的结果
        logits = torch.mean(logits,dim=1)                       # 取均值
        _, preds = torch.max(logits, 1)
        loss = criterion(logits, targets)
        correct = torch.sum(preds == targets.data)
        accuracy = correct.double() / config.batch_size
        examples_per_second = config.batch_size/float(time.time() - start_time)
        accuracies[step] = accuracy.item()
        losses[step] = loss.item()
        if step % config.print_frequency == 0:
            print("[{}] Epoch {}. Validation Step {:04d}/{:04d}, Examples/Sec = {:.2f}, "
                  "Accuracy = {:.3f}, Loss = {:.3f}".format(
                    datetime.now().strftime("%A %H:%M"), epoch+1,
                    step, steps_in_epoch, examples_per_second,
                    accuracies[step], losses[step]))
    epoch_duration = float(time.time() - epoch_start_time)
    epoch_avg_loss = np.mean(losses)
    epoch_avg_acc  = np.mean(accuracies)
    return epoch_avg_loss, epoch_avg_acc, epoch_duration